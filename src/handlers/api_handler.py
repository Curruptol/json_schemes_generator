import time
import requests
import json
from loguru import logger
import os
from configparser import ConfigParser
from typing import Optional, Any
from requests import Response
from urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class APIHandler:
    """Класс для обработки API и сохранения ответов в виде json файлов"""

    def __init__(self, config_json: dict, config_ini: ConfigParser):
        self._config_json = config_json
        self._config_ini = config_ini
        self._endpoints = self._config_json.get("ENDPOINTS")
        self._max_retries = self._config_json.get("VARIABLES").get("max_retries")

    @staticmethod
    def _save_response_json_to_dir(data: dict, file_name: str, directory: str):
        """Сохраняет ответ от API в JSON-файл.

        :param data: Данные для сохранения в файл.
        :param file_name: Имя файла для сохранения.
        :param directory: Директория для сохранения файла.

        """
        os.makedirs(directory, exist_ok=True)

        with open(os.path.join(directory, file_name), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _request_handler(self,
                         url: str,
                         method_type: str,
                         payload: Optional[dict] = None,
                         query_params: Optional[dict] = None) -> Response | None | Any:
        retries = 0

        while retries < self._max_retries:
            if method_type == "get":
                request = requests.get(url=url,
                                       params=query_params,
                                       verify=False)
                if request.status_code == 200:
                    logger.info(f"Запрос выполнен успешно, код 200")
                    return request
                else:
                    logger.warning(f"Статус код {request.status_code}. Попытка {retries + 1} / {self._max_retries}. "
                                   f"Повтор через 10 секунд...")

            elif method_type == "post":
                request = requests.post(url=url,
                                        data=json.dumps(payload),
                                        verify=False)
                if request.status_code == 200:
                    logger.info(f"Запрос выполнен успешно, код 200")
                    return request
                else:
                    logger.warning(f"Статус код {request.status_code}. Попытка {retries + 1} / {self._max_retries}. "
                                   f"Повтор через 10 секунд...")

            retries += 1
            time.sleep(10)

        logger.error(f"Максимальное количество повторов ({self._max_retries}) достигнуто. Запрос не выполнен.")

    def _api_handler(self,
                     url: str,
                     method_type: str,
                     endpoint: str,
                     file_name: str,
                     payload: Optional[dict] = None,
                     query_params: Optional[dict] = None):
        """Обработчик запросов к API.

        :param url: url для запроса.
        :param method_type: Тип запроса ('post' или 'get').
        :param endpoint: эндпоинт для запроса.
        :param file_name: наименование файла, в который будет сохранен респонс.
        :param payload: Тело для POST-запроса.
        :param query_params: Строковые параметры для GET-запроса.

        """
        if method_type == "get":
            logger.info(f"Выполнение get запроса {endpoint}")

            result_data = self._request_handler(url=url, method_type=method_type, query_params=query_params)

        elif method_type == "post":
            logger.info(f"Выполнение post запроса {endpoint}")

            result_data = self._request_handler(url=url, method_type=method_type, payload=payload)

        if result_data is not None:
            logger.info(f"Сохранение response в {self._config_json.get('API_FILES_DIR')}/{endpoint}/{file_name}")

            APIHandler._save_response_json_to_dir(data=json.loads(result_data.content.decode("utf-8")),
                                                  file_name=file_name,
                                                  directory=f"{self._config_json.get('API_FILES_DIR')}/{endpoint}")

    def _collect_response_for_weather(self):
        """Собирает успешные ответы (код 200) для weather."""
        query_params = self._config_json.get("QUERY_PARAMS_WEATHER")
        query_params.update(appid=self._config_ini.get("API_KEY", "api_key"))

        self._api_handler(url=self._config_ini.get("URL", "weather"),
                          method_type="get",
                          endpoint="weather",
                          file_name="weather.json",
                          query_params=query_params)

    def collect_responses(self):
        """Вызывает все методы для сохранения ответов для всех эндпоинтов"""
        if "weather" in self._endpoints:
            self._collect_response_for_weather()
