# Function to recognize faces
import os
import time

import cv2
from config import faces_config
from utils import read_labels


def key_pressed(key: str):
	if cv2.waitKey(1) & 0xFF == ord(key):
		return True
	return False


class FaceDetector:
	def __init__(
			self,
			camera_number: int = 0,
			detect_interval: int = 1,
	):
		self._cap = cv2.VideoCapture(camera_number)
		haar_path: str = os.path.join(faces_config.assets_path, str(faces_config.haarcascade_file_name))

		self._fc = cv2.CascadeClassifier(haar_path)

		model_file_path: str = os.path.join(faces_config.assets_path, str(faces_config.face_model_file_name))
		self._recognizer = cv2.face.LBPHFaceRecognizer.create()
		self._recognizer.read(model_file_path)

		self._users_ids = read_labels()
		self.__detect_interval = detect_interval

	def face_monitoring(self, show: bool = False):
		ret, frame = self._cap.read()
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		faces = self._fc.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))
		if show:
			cv2.imshow("Пользователь", frame)
		for (x, y, w, h) in faces:
			user_id, confidence = self._recognizer.predict(gray[y:y + h, x:x + w])
			if confidence < 50 and str(user_id) in self._users_ids.keys():
				return user_id
		return 0

	def stop_monitoring(self):
		self._cap.release()
		cv2.destroyAllWindows()

	def wait_face(self, face_name: str, timeout=10):
		if face_name not in self._users_ids.values():
			print(f'Пользователя с именем {face_name} не найдено.')
			return False
		user_id_list = list(map(int, [k for k, v in self._users_ids.items() if face_name in v]))
		start_recognize = time.perf_counter()
		print('Ожидание лица пользователя...')
		countdown = time.perf_counter() - start_recognize
		while countdown < timeout:
			countdown = time.perf_counter() - start_recognize
			print(f'\rОжидание лица пользователя...({int(timeout - countdown)})', end='')
			ret, frame = self._cap.read()
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			faces = self._fc.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))
			for (x, y, w, h) in faces:
				user_id, confidence = self._recognizer.predict(gray[y:y + h, x:x + w])
				if confidence < 50 and user_id in user_id_list:
					self._cap.release()
					cv2.destroyAllWindows()
					print('Пользователь распознан')
					return True
			cv2.imshow('Recognize Faces', frame)
		# Release the camera and close windows
		self._cap.release()
		cv2.destroyAllWindows()
		print('Таймаут.')
		return False


def detect_faces():
	"""
	Метод для распознавания лиц с камеры
	:return:
	"""
	cap = cv2.VideoCapture(faces_config.camera_number)

	haar_path: str = os.path.join(faces_config.assets_path, str(faces_config.haarcascade_file_name))
	fc = cv2.CascadeClassifier(haar_path)

	model_file_path: str = os.path.join(faces_config.assets_path, str(faces_config.face_model_file_name))
	recognizer = cv2.face.LBPHFaceRecognizer.create()
	recognizer.read(model_file_path)

	users_ids = read_labels()
	print(users_ids)
	# if name is not None:
	# 	users_ids = {k: v for k, v in users_ids.items() if name in v}
	while True:
		ret, frame = cap.read()
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		faces = fc.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100))
		for (x, y, w, h) in faces:
			user_id, confidence = recognizer.predict(gray[y:y + h, x:x + w])
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
			if confidence < 50:
				cv2.putText(frame, str(user_id), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
			else:
				cv2.putText(frame, "unknown", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
		cv2.imshow('Recognize Faces', frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	# Release the camera and close windows
	cap.release()
	cv2.destroyAllWindows()


if __name__ == '__main__':
	detect_faces()
