import logging
import sys
from loguru import logger

from src.json_schemes_generator import SOWASchemesGenerator
from src.handlers.api_handler import APIHandler
from src.configs.config import config_json, config_ini
from src.handlers.copy_json import CopyJSON


def main(from_har: bool = False, from_api: bool = False):
    """

    :param from_har: Запуск генератора json схем на основе .har файла.
    :param from_api: Запуск обработчика api и сохранение всех ответов в виде json файлов.

    """
    if from_api and not from_har:
        logger.info(f"Запуск сервиса создания json scheme")

        api_handler_instance = APIHandler(config_json=config_json, config_ini=config_ini)
        logger.info(f"Запуск api обработчика для сохранения всех необходимых респонсов")
        logger.debug(f"Вызов метода collect_responses")
        api_handler_instance.collect_responses()

        copy_json_instance = CopyJSON(config_json=config_json)
        logger.info(f"Обогащение ошибочными респонсами")
        logger.debug(f"Вызов метода copy_json_error_to_responses_dir")
        copy_json_instance.copy_json_error_to_responses_dir()

        sowa_schemes_generator_instance = SOWASchemesGenerator(is_from_api=True,
                                                               config_json=config_json)
        logger.info(f"Запуск генератора json scheme из .json файлов")
        logger.debug(f"Вызов метода build_sowa_schemes")
        sowa_schemes_generator_instance.build_sowa_schemes()

    elif from_har and not from_api:
        logger.info(f"Запуск сервиса создания json scheme")

        logger.info(f"Для .har файлов")
        sowa_schemes_generator_instance = SOWASchemesGenerator(is_from_har=True,
                                                               config_json=config_json)
        logger.info(f"Запуск генератора json scheme из .har файлов")
        sowa_schemes_generator_instance.build_sowa_schemes()

    else:
        raise ValueError(
            f"Укажите только одно True значение в аргументах from_har или from_api при вызове main() функции")

    logger.info(f"Завершение работы сервиса создания json scheme")


if __name__ == '__main__':

    logger.remove()
    logger.add(sys.stdout, colorize=True, backtrace=True, level=logging.DEBUG)

    main(from_har=False, from_api=False)
