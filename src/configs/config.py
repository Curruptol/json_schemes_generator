from dotenv import load_dotenv
import os
import configparser
import json

"""Описание объектов в config.json:

VARIABLES: параметры для парсинга .har файлов и создания json схем.
content_types: Типы контента HTTP для которых будет собрана полезная нагрузка для создания схем.
json_schema_options: Опции для атрибутов JSON схем, ограничения для разных типов данных по требованиями УЭК АПТБ.

REPLACE_PATTERNS: паттерны замен.
url: Замена UUID, переменных, прокси.
api_path: Замена UUID в пути к json схеме сервиса, токена переменной, прокси пути.

SKIP_FRAMES_LIST: Список методов для которых схемы собираться не будут.
Например, SKIP_FRAMES_LIST = [
               "fetch__qs_path_api_odag_v1_openapi",
               "fetch__qs_path_api_dataprepservice_v1_openapi",
               "xhr__qs_path_api_hub_v1_streams"]

QUERY_PARAMS_WEATHER: Строковые параметры для weather.

ENDPOINTS: список эндпоинтов для APIHandler

"""

config_ini = configparser.ConfigParser()
load_dotenv()

config_ini.add_section("URL")
config_ini.add_section("API_KEY")

config_ini.set("URL", "weather", f"{os.getenv('URL')}weather")

config_ini.set("API_KEY", "api_key", f"{os.getenv('API_KEY')}")

config_json_path = os.path.join(os.path.dirname(__file__), "config.json")
config_ini_path = os.path.join(os.path.dirname(__file__), "config.ini")

with open(config_json_path, encoding="UTF-8") as f:
    config_json = json.load(f)

with open(config_ini_path, 'w') as config_file:
    config_ini.write(config_file)

config_ini.read(config_ini_path)
