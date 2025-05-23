import os
import subprocess
from pathlib import Path
from typing import Dict

import psutil
import pydub

from config import faces_config, voice_config
import json


def kill_process_by_name(name: str):
    for process in psutil.process_iter():
        if process.name() == name:
            process.kill()


def get_vosk_model_path():
    if not os.path.exists(voice_config.vosk_models_path):
        raise FileNotFoundError(
            f"Директория с моделями VOSK не найдена: {voice_config.vosk_models_path}"
        )
    models = list(
        filter(
            lambda s: "vosk" in s.lower() and ".zip" not in s.lower(),
            os.listdir(voice_config.vosk_models_path),
        )
    )
    models = {
        model: sum(
            file.stat().st_size
            for file in Path(
                str(os.path.join(voice_config.vosk_models_path, model))
            ).rglob("*")
            if file.is_file()
        )
        for model in models
    }
    c = 0
    for model, size in models.items():
        print(f"{c + 1}. {model} ({size // 1024 ** 2:.0f} МБ)")
        c += 1
    index_str = input("Введите номер модели распознавания: ")
    if index_str.isdigit():
        index = int(index_str)
        return list(models.keys())[index - 1]
    return "NO_MODEL"


def humanize_time(time_at_work):
    days = time_at_work // 86400
    hours = (time_at_work - days * 86400) // 3600
    minutes = (time_at_work - days * 86400 - hours * 3600) // 60
    seconds = time_at_work - days * 86400 - hours * 3600 - minutes * 60
    human_time = f"{int(seconds)} секунд" if seconds > 0 else ""
    human_time = (f"{int(minutes)} минут" if minutes > 0 else "") + human_time
    human_time = (f"{int(hours)} часов" if hours > 0 else "") + human_time
    human_time = (f"{int(days)} дней" if days > 0 else "") + human_time
    if len(human_time) > 0:
        return human_time
    else:
        return "Мало времени"


def check_audio_playing_status():
    res = subprocess.check_output(["pmset", "-g"]).decode()
    res = res[res.find("\n sleep") :].replace("\n", "", 1)
    res = res[: res.find("\n")]
    res = res[res.find("(") + 1 : res.find(")")]
    print(res)
    result = res.count(",")
    print(result > 3)


def read_labels() -> Dict:
    labels_path: str = os.path.join(
        str(faces_config.assets_path), str(faces_config.labels_file_name)
    )
    if not os.path.exists(labels_path):
        raise FileNotFoundError(f"Labels file not found at {labels_path}")
    data: Dict = json.load(open(labels_path))
    return data


def save_labels(data: Dict) -> None:
    labels_path: str = os.path.join(
        str(faces_config.assets_path), str(faces_config.labels_file_name)
    )

    with open(labels_path, "w") as f:
        json.dump(data, f)


def write_file_content(file_path: str, content: str):
    with open(file_path, "w") as f:
        f.write(content)


def convert_audio_file(file_path: str, audio_format: str) -> None:
    audio_file = pydub.AudioSegment.from_file(file_path)
    file_ext = file_path.split(".")[-1].lower()
    audio_file.export(
        file_path.replace("." + file_ext, "." + audio_format), format=audio_format
    )


def split_by_silence(
    file_path: str,
    min_sound_len: int = 1000,
    min_db: float = -80.0,
) -> list:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден!")
    audio_file = pydub.AudioSegment.from_file(file_path)
    print(f"Длительность записи: {audio_file.duration_seconds} секунд, ", end="")
    parts, offset, part_offset = 0, 0, 0
    files_paths = list()
    chunk_size = 100
    while True:
        end_index = (
            (offset + chunk_size)
            if offset + chunk_size < len(audio_file)
            else len(audio_file)
        )
        if end_index - offset < chunk_size:
            # print(f"Осталось {end_index - offset} мс, записываем последний отрезок и выходим из цикла")
            last_file_path: str = file_path.replace(
                "." + file_path.split(".")[-1], f"_{parts + 1}_end.wav"
            )
            files_paths.append(last_file_path)
            last_part = audio_file[part_offset:]
            last_part.export(last_file_path, format="wav")
            parts += 1
            break
        audio_part = audio_file[offset:end_index]
        if audio_part.dBFS < min_db:
            # print(f"Найдена тишина на моменте {offset} мс")
            if offset + int(chunk_size / 5) - part_offset < min_sound_len:
                # print(f"Но пропущена изза слишком короткого отрезка = {offset - part_offset} мс")
                offset += chunk_size
                continue
            out_part = audio_file[part_offset : offset + int(chunk_size / 5)]
            out_file_path: str = file_path.replace(
                "." + file_path.split(".")[-1], f"_{parts + 1}.wav"
            )
            files_paths.append(out_file_path)
            out_part.export(out_file_path, format="wav")
            # print(f"Отрезок длиной {offset - part_offset} мс записан")
            offset += int(4 * chunk_size / 5)
            # print(f"Начинаем слушать с момента {offset} мс")
            # print("=" * 100)
            part_offset = offset
            parts += 1
        else:
            offset += chunk_size
    print(f"файл разбит на {parts} отрезков.")
    return files_paths


if __name__ == "__main__":
    # check_audio_playing_status()
    # convert_audio_file(
    # 	file_path=r'/Users/bioxakep/IdeaProjects/KevinAssistant/audio_files/FROM_TEXT_20250521081840.ogg',
    # 	audio_format='wav'
    # )
    files = split_by_silence(
        file_path=r"/Users/bioxakep/IdeaProjects/KevinAssistant/audio_files/FROM_TEXT_20250521081840.wav",
        min_sound_len=10000,
    )
