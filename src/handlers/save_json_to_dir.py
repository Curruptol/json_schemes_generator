import json
import os
from requests import Response


class SaveJSONToDir:
    """Сохраняет ответ от API в JSON-файл."""

    @staticmethod
    def save_json_to_dir(data: Response, file_name: str, directory: str):
        """Сохраняет ответ от API в JSON-файл.

        :param data: Данные класса requests.Response для сохранения в файл.
        :param file_name: Имя файла для сохранения.
        :param directory: Директория для сохранения файла.

        """
        data = json.loads(data.content.decode("utf-8"))

        os.makedirs(directory, exist_ok=True)

        with open(os.path.join(directory, file_name), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
