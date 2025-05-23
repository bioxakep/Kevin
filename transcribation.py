import os
import sys
from utils import get_vosk_model_path, split_by_silence
from voices import VoiceRecognizer, VoiceRecognizerResult


def transcribe(
    voice_path: str,
    frame_rate: int = VoiceRecognizer.FREQ_16,
    min_sound_len: int = 10000,
):
    # Выбираем модель транскрибации
    selected_model = get_vosk_model_path()
    if not "vosk" in selected_model:
        raise Exception("Не выбрана модель для транскрибации")
    vr = VoiceRecognizer(selected_model)

    # Собираем файлы для транскрибации
    if not os.path.exists(voice_path):
        raise Exception("Указанный путь не существует")
    files_to_transcribe = list()
    if os.path.isdir(voice_path):
        for _file in os.listdir(voice_path):
            if _file.endswith(".wav"):
                files_to_transcribe.append(os.path.join(sys.argv[1], _file))
    else:
        files_to_transcribe.append(voice_path)
    if len(files_to_transcribe) == 0:
        raise Exception("Указанный путь не содержит файлов .wav")
    # Транскрибируем файлы
    print(f"Начинаем транскрибацию {len(files_to_transcribe)} файлов")
    for audio_file_path in files_to_transcribe:
        print(f"Начинаем транскрибацию файла {audio_file_path}")

        result_text_path: str = audio_file_path.split(".")[0] + "_transcribed_text.txt"
        transcribe_result: VoiceRecognizerResult = vr.recognize_wav(
            audio_file_path,
            frame_rate=frame_rate,
        )
        if transcribe_result.status != VoiceRecognizer.STATUS_TOO_LONG:
            with open(result_text_path, "w") as result_file:
                result_file.write(transcribe_result.result)
                print(f"Транскрибация файла {audio_file_path} завершена")
                continue
        recognized_parts = list()
        audio_parts_paths = split_by_silence(
            audio_file_path, min_sound_len=min_sound_len
        )
        for part_path in audio_parts_paths:
            transcribe_part_result: VoiceRecognizerResult = vr.recognize_wav(
                part_path,
                frame_rate=frame_rate,
            )
            recognized_parts.append(transcribe_part_result.result)
            os.remove(part_path)
        file_recognized_text = " ".join(recognized_parts)
        with open(result_text_path, "w") as result_file:
            result_file.write(file_recognized_text)
        print(f"Транскрибация файла {audio_file_path} по частям завершена")


if __name__ == "__main__":
    transcribe(
        voice_path=sys.argv[1],
        # min_sound_len=10000,
    )
