import audioop
import logging
import sys
import time
import pyaudio  # brew install portaudio
from collections import deque
from logging import getLogger
import speech_recognition as sr
recorder_logger = getLogger(__name__)
recorder_logger.setLevel(logging.ERROR)
recorder_logger.addHandler(logging.StreamHandler(sys.stdout))


class VoiceRecorder:
	""" Запись голоса с микрофона """
	CHUNK = 2048
	FRAME_RATE = 16000
	SAMPLE_WIDTH = 2

	def __init__(self):
		self._audio = pyaudio.PyAudio()
		self.__noise_params = self.calibrate()
		recorder_logger.info(f'Распознавание инициализировано (MIN: {self.min_volume} | MAX: {self.max_volume})')

	def init_stream(self):
		return self._audio.open(
			input=True,
			start=True,
			channels=1,
			format=pyaudio.paInt16,
			rate=VoiceRecorder.FRAME_RATE,
			frames_per_buffer=VoiceRecorder.CHUNK
		)

	def calibrate(self):
		volume_values_window_size = 10
		volume_deque = deque(maxlen=volume_values_window_size)
		stream = self.init_stream()
		for i in range(volume_values_window_size):
			frame = stream.read(VoiceRecorder.CHUNK)
			pre_rms_value = audioop.rms(frame, VoiceRecorder.SAMPLE_WIDTH)
			volume_deque.appendleft(pre_rms_value)
		stream.stop_stream()
		stream.close()
		del stream
		return volume_deque

	def get_audio_command(self, timeout: float = 1):
		frames = bytearray()
		stream = self.init_stream()
		frame = stream.read(VoiceRecorder.CHUNK)
		volume = audioop.rms(frame, VoiceRecorder.SAMPLE_WIDTH)
		start_wait = time.perf_counter()
		recorder_logger.info('- жду команду')
		while volume < 2 * self.max_volume:
			frame = stream.read(VoiceRecorder.CHUNK)
			volume = audioop.rms(frame, VoiceRecorder.SAMPLE_WIDTH)
			if time.perf_counter() - start_wait > timeout:
				recorder_logger.info('- не дождался команды')
				return frames
		recorder_logger.info('- записываю команду')
		frames.extend(frame)
		start_pause = -1
		recording = True
		while recording:
			now = time.perf_counter()
			frame = stream.read(VoiceRecorder.CHUNK)
			volume = audioop.rms(frame, VoiceRecorder.SAMPLE_WIDTH)
			frames.extend(frame)
			if volume < 2 * self.max_volume:
				if start_pause < 0:
					start_pause = now
					recorder_logger.info('- пауза записи команды')
				elif now - start_pause >= 1:
					recorder_logger.info('- остановка записи команды по времени')
					recording = False
			else:
				if start_pause > 0:
					start_pause = -1
					recorder_logger.info('- продолжаю запись команды')
		stream.stop_stream()
		stream.close()
		out_data = sr.AudioData(
			frame_data=frames,
			sample_rate=VoiceRecorder.FRAME_RATE,
			sample_width=VoiceRecorder.SAMPLE_WIDTH
		).get_wav_data()
		return out_data

	def yield_commands(self, timeout: int = 15):
		"""
		Запись и передача команд по очереди до превышения таймаута в тишине.
		:param timeout: измеряется в секундах
		:return: фрэймы аудиозаписи
		"""
		frames = bytearray()
		start_record = -1
		last_record = -1
		start_pause = -1
		recording = False
		stream = self.init_stream()
		stream.start_stream()
		while True:
			now = time.perf_counter()
			frame = stream.read(VoiceRecorder.CHUNK)
			volume = audioop.rms(frame, VoiceRecorder.SAMPLE_WIDTH)
			# print(f'\rMIN: {self.min_volume} | MAX: {self.max_volume} | VOL: {volume}', end="\t")
			if not recording:
				if (volume - self.min_volume) // (1 + self.max_volume - self.min_volume) >= 2:
					recording = True
					frames.extend(frame)
				else:
					self.__noise_params.pop()
					self.__noise_params.appendleft(volume)
				if now - last_record > timeout and last_record > 0:
					break
			else:
				frames.extend(frame)
				if volume <= 2 * self.max_volume:
					if start_pause < 0:
						start_pause = now
					elif now - start_pause >= 0.5:
						stream.stop_stream()
						yield sr.AudioData(
							frame_data=frames,
							sample_rate=VoiceRecorder.FRAME_RATE,
							sample_width=VoiceRecorder.SAMPLE_WIDTH
						).get_wav_data()
						last_record = time.perf_counter()
						stream.start_stream()
						frames.clear()
						recording = False
				else:
					if start_pause > 0:
						start_pause = -1
		# Stop and close the stream
		stream.stop_stream()
		stream.close()
		self._audio.terminate()

	def stop(self):
		self._audio.terminate()

	@property
	def min_volume(self):
		return min(self.__noise_params)

	@property
	def max_volume(self):
		return max(self.__noise_params)
