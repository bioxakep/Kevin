import json
import os
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer
from config import voice_config
from utils import get_vosk_model_path


class VoiceRecognizerResult:
    __slots__ = ("status", "result")

    def __init__(self, status: str, result: str = ""):
        self.status = status
        self.result = result


class VoiceRecognizer:
    FREQ_16 = 16000
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    STATUS_TOO_LONG = "TOO_LONG"
    STATUS_OK = "OK"

    def __init__(self, model_path: str):
        """Инициализация модели распознавания с установкой частоты дискретизации аудиопотока"""
        print(f"Инициализация модели распознавания: {model_path}")
        self.__model = Model(os.path.join(voice_config.vosk_models_path, model_path))
        self.__recognizer = KaldiRecognizer(self.__model, VoiceRecognizer.FREQ_16)
        # self.__result = str()
        # AudioSegment.converter = '/opt/homebrew/Cellar/ffmpeg/7.0_1/bin/ffmpeg'

    def __recognize_it(self, raw_data, empty_result: str = ""):
        try:
            self.__recognizer.AcceptWaveform(raw_data)
        except Exception as ex:
            print("Ошибка транскрибации аудио:" + ex.args[0])
            return ""
        ru_res = json.loads(self.__recognizer.FinalResult())
        if "text" in ru_res.keys():
            return ru_res.get("text")
        return empty_result

    def recognize_ogg(self, ogg_file_path: str):
        voice_wav_path = os.path.join(
            voice_config.audio_files,
            os.path.basename(ogg_file_path.replace(".ogg", ".wav")),
        )
        audio = AudioSegment.from_ogg(ogg_file_path)
        audio = audio.set_sample_width(2).set_frame_rate(16000)
        audio.export(voice_wav_path, format="wav")
        audio = AudioSegment.from_wav(voice_wav_path)
        self.__recognizer.AcceptWaveform(audio.raw_data)
        os.remove(voice_wav_path)
        ru_res = json.loads(self.__recognizer.FinalResult())
        if "text" in ru_res.keys():
            return f"Распознан текст: {ru_res.get('text')}"
        return "Не распознано."

    def recognize_wav(
        self,
        wav_file_path: str,
        max_audio_duration: int = 30,
        frame_rate: int = 16000,
    ) -> VoiceRecognizerResult:
        audio = AudioSegment.from_wav(wav_file_path)
        if audio.sample_width > 2:
            audio = audio.set_sample_width(2).set_frame_rate(frame_rate)
        else:
            audio = audio.set_sample_width(1).set_frame_rate(frame_rate)
        if audio.duration_seconds > max_audio_duration:
            return VoiceRecognizerResult(VoiceRecognizer.STATUS_TOO_LONG)
        recognized_text = self.__recognize_it(
            audio.raw_data, empty_result="не распознано."
        )
        return VoiceRecognizerResult(VoiceRecognizer.STATUS_OK, recognized_text)

    def recognize_mp3(self, mp3_file_path: str):
        if not os.path.exists(voice_config.audio_files):
            os.makedirs(voice_config.audio_files)
        voice_wav_path = os.path.join(
            voice_config.audio_files,
            os.path.basename(mp3_file_path.replace(".mp3", ".wav")),
        )
        audio = AudioSegment.from_mp3(mp3_file_path)
        audio = audio.set_sample_width(1).set_frame_rate(16000)
        audio.export(voice_wav_path, format="wav")
        audio = AudioSegment.from_wav(voice_wav_path)
        self.__recognizer.AcceptWaveform(audio.raw_data)
        # os.remove(voice_wav_path)
        ru_res = json.loads(self.__recognizer.FinalResult())
        if "text" in ru_res.keys():
            return f"Распознан текст: {ru_res.get('text')}"
        return "Не распознано."

    def recognize_from_micro(self, audio_data):
        try:
            self.__recognizer.AcceptWaveform(audio_data)
        except TypeError:
            return ""
        # os.remove(voice_wav_path)
        ru_res = json.loads(self.__recognizer.FinalResult())
        if "text" in ru_res.keys():
            return ru_res.get("text")
        return ""


if __name__ == "__main__":
    selected_model = get_vosk_model_path()
    if not "vosk" in selected_model:
        raise Exception("Не выбрана модель для транскрибации")
    vr = VoiceRecognizer(selected_model)
    test_wav_file_path: str = (
        r"/Users/bioxakep/IdeaProjects/.../FROM_TEXT_20250521081840.wav"
    )
    text = vr.recognize_wav(
        wav_file_path=r"/Users/bioxakep/IdeaProjects/.../russian_speech.wav",
        max_audio_duration=20,
        frame_rate=VoiceRecognizer.FREQ_16,
    )
    recognized_file_path: str = test_wav_file_path.replace(".wav", "_recognized.txt")
    with open(recognized_file_path, "w") as f:
        f.write(text.result)
