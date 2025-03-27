from typing import Optional, List
import json
import jsonref
import os
import os.path
import re
from urllib.parse import urlparse
from haralyzer import HarParser
from loguru import logger
from configparser import ConfigParser

from src.recorder.recorder import Recorder
from src.handlers.merge_json_schemes import MergeJSONSchemes
from src.handlers.deduplicate_array_elements import ArrayElementDeduplicator


class SOWASchemesGenerator:
    """Создание JSON схем на основе данных из .har файлов и openjson схем."""

    def __init__(self,
                 config_json: dict,
                 is_from_har: bool = False,
                 is_from_api: bool = False,
                 skip_frames_list: Optional[List[str]] = None):
        """Инициализация генератора конфигурации SOWA.

        :param skip_frames_list: Список игнорируемых методов в har файле.
        :param is_from_har: Читать .har файлы.
        :param is_from_api: Читать .json файлы.

        """
        self.is_from_har = is_from_har
        self.is_from_api = is_from_api

        self.dump_files_list = []
        if self.is_from_har:
            self.path_to_dump_files = config_json.get("HAR_FILES_DIR")
        elif self.is_from_api:
            self.path_to_dump_files = config_json.get("API_FILES_DIR")

        for root, _, files in os.walk(self.path_to_dump_files):
            for file in files:
                if ".json" in file or ".har" in file:
                    self.dump_files_list.append(os.path.join(root, file))
        logger.debug(f"Файлы для чтения: {self.dump_files_list}")

        self.path_to_schemes_dir = config_json.get("JSON_SCHEMES_DIR")
        self.variables = config_json.get("VARIABLES")
        self.replace_patterns = config_json.get("REPLACE_PATTERNS")

        self.skip_frames_list = skip_frames_list

    @staticmethod
    def read_dump_file(path_to_dump_file: str, as_json: bool = False) -> dict:
        """Чтение содержимого .har или .json файла.

        :param path_to_dump_file: Путь к файлу.
        :param as_json: Преобразовывать ли содержимое в JSON.
        :return: Содержимое файла в виде строки или словаря.

        """
        with open(path_to_dump_file, "r", encoding="UTF-8") as file:
            file_data = file.read()

            if as_json:
                return json.loads(file_data)
            else:
                return file_data

    @staticmethod
    def create_schema_dir(path_to_schema: str, path_to_schemes_dir: str) -> str:
        """Создание для сохранение схем.

        :param path_to_schema: Относительный путь к схеме.
        :param path_to_schemes_dir: Основной каталог для схем.
        :return: Абсолютный путь к каталогу схемы.

        """
        normalized_path = os.path.splitext(os.path.join(*path_to_schema.split("/")))[0]
        path_to_schema = os.path.abspath(os.path.join(path_to_schemes_dir, normalized_path))
        os.makedirs(path_to_schema, exist_ok=True)
        logger.info(f"Создание директории для сохранения схем: {path_to_schema[path_to_schema.find('schemes')::]}")

        return path_to_schema

    def set_path_to_schema(self, frame: dict) -> dict:
        """Установка путей к схемам для каждого этапа кадра.

        :param frame: Кадр запроса.
        :return: Кадр с установленными путями к схемам.

        """
        for stage, schemas in frame["schemes"].items():
            for method, schema in schemas.items():
                api_path = f'{frame["api_path"].split("/")[-1]}/'

                relative_schema_path = "/".join(
                    ["".join([self.path_to_schemes_dir, os.path.splitext(api_path)[0]]), f"{stage}.json"]
                )

                absolute_schema_dir_path = self.create_schema_dir(path_to_schema=api_path,
                                                                  path_to_schemes_dir=self.path_to_schemes_dir)
                absolute_schema_path = os.path.join(absolute_schema_dir_path, f"{stage}.json")
                logger.info(f"Файл для сохранения: {absolute_schema_path[absolute_schema_path.find('schemes')::]}")

                frame["schemes"][stage][method] = {}

                frame["schemes"][stage][method]["schema"] = schema
                frame["schemes"][stage][method]["relative_schema_path"] = relative_schema_path
                frame["schemes"][stage][method]["absolute_schema_path"] = absolute_schema_path

        return frame

    def convert_payload_to_schema(self, payload_type: str, payload: str) -> Optional[str]:
        """Конвертирование полезной нагрузки кадра в JSON схему.

        :param payload_type: Тип данных кадра.
        :param payload: Полезная нагрузка кадра.
        :return: JSON схема или None, если конвертация невозможна.

        """

        if payload_type == "json_data":
            if len(payload) == 0:
                payload = json.dumps({})

            request_schema_generator = Recorder.from_str(payload)
            json_schema = request_schema_generator.generator.to_json(self.variables["json_schema_options"])
            return json_schema
        else:
            return None

    def str_replace(self, string: str, replace_method: str) -> str:
        """Замена подстрок в строке согласно заданному шаблону.

        :param string: Исходная строка.
        :param replace_method: Метод замены, описанный в replace_patterns.
        :return: Строка после замены.

        """
        for replace in self.replace_patterns[replace_method]:
            string = re.sub(
                replace["pattern"],
                replace["replace"],
                string
            )

        return string

    def build_sowa_schemes(self):
        """Точка входа для генератора"""
        # Получение списка запросов из дампов
        logger.debug(f"Вызов метода parse_dump_file, получение entries")
        entries = self.parse_dump_file()

        # Получение списка кадров для каждого запроса
        logger.debug(f"Вызов метода get_frames, получение frames")
        frames = self.get_frames(entries=entries)

        # Объединение кадров запросов по методу и адресу
        logger.debug(f"Вызов метода merge_frames, получение merged_frames")
        merged_frames = self.merge_frames(frames=frames)

        # Сохранение каждой схемы в директорию
        for frame_name, frame in merged_frames.items():
            logger.debug(f"Вызов метода set_path_to_schema")
            frame = self.set_path_to_schema(frame=frame)
            logger.debug(f"Вызов метода write_schema")
            SOWASchemesGenerator.write_schema(frame=frame)

    def parse_dump_file(self) -> list:
        """Разбор файлов дампов для получения списка запросов.

        :return: Список запросов.

        """
        entries = []

        for path_to_dump_file in self.dump_files_list:

            logger.info(f"Парсинг файла: {path_to_dump_file}")

            if os.path.splitext(path_to_dump_file)[1] == ".har":
                dump_data = self.read_dump_file(path_to_dump_file=path_to_dump_file, as_json=True)
                har_parser_instance = HarParser(dump_data)

                for entry in har_parser_instance.har_data["entries"]:
                    request_url = entry["request"]["url"]
                    api_path = urlparse(request_url).path

                    if entry["_resourceType"] == "xhr":
                        entries.append({"type": "har", "api_path": api_path, "package": entry})

            elif os.path.splitext(path_to_dump_file)[1] == ".json":
                dump_data = self.read_dump_file(path_to_dump_file=path_to_dump_file)
                api_dict = jsonref.JsonRef.replace_refs(json.loads(json.dumps(jsonref.loads(dump_data), default=dict)))
                path_to_dump_file = path_to_dump_file.replace("\\", "/")
                api_path = path_to_dump_file.split("/")[3]
                dump_file_name = path_to_dump_file[(path_to_dump_file.find("dumps"))::]
                entries.append({"type": "api", "api_path": api_path, "dump_file_name": dump_file_name,
                                "package": api_dict})

            else:
                continue

        return entries

    def get_frames(self, entries: list) -> list:
        """Получение списка кадров запроса со схемами
        {
            'type': resource_type,
            'method': method,
            'url': url,
            'api_path': api_path,
            'schemes':
                {
                    'request': request_schemas,
                    'response': response_schemas
                }
        }

        :param entries: Список запросов
        :return: Список кадров со схемами

        """
        frames = []

        if self.is_from_har:

            for entry in entries:

                # Преобразование URL адреса и базового пути к схеме
                url = self.str_replace(string=entry["api_path"], replace_method="url")
                api_path = self.str_replace(string=entry["api_path"], replace_method="api_path")

                logger.info(f"URL: {api_path}")

                request_schemas = []
                response_schemas = []

                if entry["type"] == "har":
                    if entry["package"]["_resourceType"] in ["xhr", "fetch"]:
                        resource_type = "fetch"
                    else:
                        resource_type = entry["package"]["_resourceType"]

                    method = entry["package"]["request"]["method"].lower()
                    response_content_type = ""

                    for header in entry["package"]["response"]["headers"]:
                        if header["name"] == "Content-Type":
                            response_content_type = header["value"]

                    name_with_extension = os.path.splitext(api_path[1::])
                    if name_with_extension[1] != "":
                        # Если это файл с расширением - пропуск записи, тк это статика, она не описывается схемой
                        continue

                    # Для HTTP записи
                    if resource_type == "fetch" and response_content_type in self.variables["content_types"]:
                        # Получение тела запроса
                        try:
                            request_json_str = json.dumps(entry["package"]["request"]["postData"]["text"])
                        except KeyError:
                            request_json_str = ""

                        request_schema = self.convert_payload_to_schema(payload_type="json_data",
                                                                        payload=request_json_str)
                        request_schemas.append(request_schema)

                        # Получение тела ответа
                        try:
                            response_json_str = entry["package"]["response"]["content"]["text"]
                        except KeyError:
                            response_json_str = ""

                        response_schema = self.convert_payload_to_schema(payload_type="json_data",
                                                                         payload=response_json_str)
                        response_schemas.append(response_schema)

                    frames.append(
                        {
                            "type": resource_type,
                            "method": method,
                            "url": url,
                            "api_path": api_path,
                            "schemes":
                                {
                                    "request": request_schemas,
                                    "response": response_schemas
                                }
                        }
                    )
        elif self.is_from_api:
            for entry in entries:
                url = "/api/v2/" + entry.get("api_path")
                api_path = url

                logger.info(f"Создание схемы для файла: {entry['dump_file_name']}")

                request_schemas = []
                response_schemas = []
                resource_type = "fetch"

                method = "get"

                request_json_str = ""
                request_schema = self.convert_payload_to_schema(payload_type="json_data",
                                                                payload=request_json_str)
                request_schemas.append(request_schema)

                response_json_str = json.dumps(entry.get("package"), ensure_ascii=False)
                response_schema = self.convert_payload_to_schema(payload_type="json_data",
                                                                 payload=response_json_str)
                response_schemas.append(response_schema)

                frames.append({
                    "type": resource_type,
                    "method": method,
                    "url": url,
                    "api_path": api_path,
                    "schemes": {
                        "request": request_schemas,
                        "response": response_schemas
                    }
                }
                )

        return frames

    def merge_frames(self, frames: list) -> dict:
        """Объединение кадров по методу и адресу запроса.

        :param frames: Список кадров.
        :return: Объединённые кадры запросов.

        """
        merged_frames = {}

        for frame in frames:
            # Формирование имени объединенного кадра
            frame_name = f"{frame['type']}__{frame['api_path'][1::].replace('/', '_')}"
            frame["name"] = frame_name

            # Объединение схем текущего кадра
            for stage, schemas_list in frame["schemes"].items():
                merged_schema = MergeJSONSchemes.merge_schemes_by_jsonmerge(schemes=frame["schemes"][stage])
                frame["schemes"][stage] = {}
                frame["schemes"][stage][frame["method"]] = merged_schema

                # Если в списке объединенных кадров есть кадр с таким же именем,
                # то объединение схем с объединенным кадром
                if frame_name in merged_frames:
                    if merged_frames[frame_name]["schemes"][stage].get(frame["method"]):
                        merged_frames[frame_name]["schemes"][stage][
                                frame["method"]] = MergeJSONSchemes.merge_schemes_by_jsonmerge(
                                schemes=[frame["schemes"][stage][frame["method"]],
                                         merged_frames[frame_name]["schemes"][stage][frame["method"]]
                                         ]
                            )
                    else:
                        merged_frames[frame_name]["schemes"][stage][frame["method"]] = merged_schema

                else:
                    # Если кадра нет в списке объединенных, то добавление кадра
                    merged_frames[frame_name] = frame

        return merged_frames

    @staticmethod
    def write_schema(frame: dict):
        """Запись схем в директорию со схемами

        :param frame: Кадр запроса

        """
        for stage, schemas in frame["schemes"].items():
            for method, schema in schemas.items():
                with open(schema["absolute_schema_path"], "w") as json_schema_file:
                    logger.info(
                        f"Сохранение файла: "
                        f"{schema['absolute_schema_path'][(schema['absolute_schema_path'].find('schemes'))::]}")
                    json_schema_file.write(schema["schema"])
                    logger.info(f"Файл сохранен")
