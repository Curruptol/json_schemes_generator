import json
from loguru import logger
import os


class CopyJSON:
    """Класс для копирования json из конфига в директорию проекта"""

    def __init__(self, config_json: dict):
        self.json_error_400 = config_json.get("RESPONSE_ERROR_400")
        self.path_to_api = config_json.get("API_FILES_DIR")

    def copy_json_error_to_responses_dir(self):
        """Метод копирует ошибочные респонсы из конфига в каталог с респонсами каждого эндпоинта"""

        endpoints_dirs = next(os.walk(self.path_to_api))[1]

        logger.debug(f"Копирование респонсов с ошибками в директории эндпоинтов = {endpoints_dirs}")

        for trg_dir in endpoints_dirs:
            if not os.path.exists(f"{self.path_to_api}/{trg_dir}/error_400.json"):
                with open(f"{self.path_to_api}/{trg_dir}/error_400.json", 'w', encoding='utf-8') as file:
                    json.dump(self.json_error_400, file, ensure_ascii=False, indent=4)

                    logger.debug(f"error_400.json сохранен в {self.path_to_api}/{trg_dir}/")

            else:
                logger.debug(f"{self.path_to_api}/{trg_dir}/error_400.json уже существует")

        logger.info(f"Завершено копирование ошибочных респонсов")
