import os.path
from PIL import Image
import numpy as np
import cv2
# pip install opencv-python
# pip install opencv_contrib_python

from config import faces_config
from utils import save_labels


def read_faces():
	"""
	Метод для сохранения фото лиц пользователей с камеры для обучения модели распознавания
	:return: Файлы с фотоизображениями лица пользователей и файл с их именами
	"""
	users_labels = dict()
	while True:
		name = input("Введите ваше имя: ")
		next_key = str(len(users_labels) + 1)  # нумерация пользователей начинается с 1
		users_labels[next_key] = name
		input(
			"Необходимо получить несколько фотографий вашего лица для обучения. "
			"Нажмите Enter как будете готовы к фотосессии."
		)
		read_face(next_key)
		# if 'Y' in input("Носите ли вы очки? (Y | N)"):
		# 	input(
		# 		"Необходимо получить несколько фотографий вашего лица в очках. "
		# 		"Нажмите Enter как будете готовы к фотосессии."
		# 	)
		# 	next_key = str(len(users_labels) + 1)  # нумерация пользователей начинается с 1
		# 	users_labels[next_key] = name + "_glasses"
		# 	read_face(next_key)
		# Спрашиваем про очки, повторяем процедуру при их наличии и сохраняем фото с именем + "_glasses"
		# Спрашиваем, будут ли еще пользователи (Y\N) и выходим если нет
		if 'N' in input("Будут ли еще пользователи? (Y | N)"):
			break
	train_model()
	save_labels(users_labels)
	print('Модель обучена и сохранена.')
	print(f'Теперь она позволяет распознавать {len(users_labels.keys())} пользователей.')


def read_face(face_number: str):
	"""
	Метод для сохранения фото лица конкретного пользователя
	:return: Файлы с фотоизображениями лица пользователя
	"""
	# указываем, что мы будем искать лица по примитивам Хаара
	detector = cv2.CascadeClassifier(os.path.join(
		str(faces_config.assets_path),
		str(faces_config.haarcascade_file_name))
	)
	frame = 0  # счётчик изображений
	offset = 50  # расстояния от распознанного лица до рамки
	video = cv2.VideoCapture(faces_config.camera_number)
	while True:
		ret, im = video.read()  # считываем кадр
		gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)  # переводим всё в ч/б для простоты
		# настраиваем параметры распознавания и получаем лица с кадра
		faces = detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))
		for (x, y, w, h) in faces:
			frame = frame + 1
			# записываем файл на диск
			face_image_name: str = "face-" + face_number + '.' + str(frame)
			face_image_file_path: str = os.path.join(
				str(faces_config.faces_dataset_folder),
				face_image_name + ".jpg"
			)
			face_data = gray[y - offset:y + h + offset, x - offset:x + w + offset]
			try:
				cv2.imwrite(face_image_file_path, face_data)
			except:
				continue
			# формируем размеры окна для вывода лица
			cv2.rectangle(im, (x - offset, y - offset), (x + w + offset, y + h + offset), (225, 0, 0), 2)
			# показываем очередной кадр, который мы запомнили
			cv2.imshow(f'Face {face_number}', im[y - offset:y + h + offset, x - offset:x + w + offset])
			# делаем паузу
			cv2.waitKey(50)
			print(f'\rДелаем фото...{100 * frame/faces_config.train_frames_count:0.0f}', end='')
		# если у нас хватает кадров
		if frame > faces_config.train_frames_count:
			# освобождаем камеру
			video.release()
			# удаляем все созданные окна
			cv2.destroyAllWindows()
			# останавливаем цикл
			break


# получаем картинки и подписи из датасета
def train_model():
	"""
	Метод для обучения модели распознавания лиц из файлов с фотографиями лиц пользователей
	:return: Обученная модель распознавания лиц
	"""
	# списки картинок и подписей на старте пустые
	haar_path: str = os.path.join(faces_config.assets_path, str(faces_config.haarcascade_file_name))
	fc = cv2.CascadeClassifier(haar_path)
	images = []
	labels = []
	count = 0
	image_files = os.listdir(faces_config.faces_dataset_folder)
	total_images = len(image_files)
	for image_file_name in image_files:
		image_path = os.path.join(faces_config.faces_dataset_folder, image_file_name)
		# читаем картинку и сразу переводим в ч/б
		image = Image.open(image_path).convert('L')
		# переводим картинку в numpy-массив
		image_np = np.array(image, 'uint8')
		# получаем id пользователя из имени файла
		nbr = int(image_file_name.split(".")[0].replace("face-", ""))
		# определяем лицо на картинке
		faces = fc.detectMultiScale(image_np)
		# если лицо найдено
		for (x, y, w, h) in faces:
			# добавляем его к списку картинок
			images.append(image_np[y: y + h, x: x + w])
			# добавляем id пользователя в список подписей
			labels.append(nbr)
			# выводим текущую картинку на экран
			# cv2.imshow("Loading...", image_np[y: y + h, x: x + w])
			# делаем паузу
			cv2.waitKey(50)
			print(f'\rДобавляем фото в обучающую выборку...{count}/{total_images}', end='')
			count += 1
	recognizer = cv2.face.LBPHFaceRecognizer.create()
	# обучаем модель распознавания на наших картинках и учим сопоставлять её лица и подписи к ним
	print('\nОбучаем модель...')
	recognizer.train(images, np.array(labels))
	model_file_path: str = os.path.join(faces_config.assets_path, str(faces_config.face_model_file_name))
	recognizer.save(model_file_path)
	cv2.destroyAllWindows()


if __name__ == '__main__':
	read_faces()
