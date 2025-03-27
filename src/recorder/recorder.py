from src.generator.generator import SchemaGenerator


class Recorder(object):
    """Класс для записи и сохранения схем JSON-схем."""

    def __init__(self, generator: SchemaGenerator):
        """Конструктор класса.

        :param generator: Экземпляр класса `SchemaGenerator` для работы со схемой.

        """
        self.generator = generator

    @classmethod
    def from_str(cls, json_string: str):
        """Создает экземпляр класса на основе строки JSON.

        :param json_string: Строка JSON, содержащая данные.
        :return: Экземпляр класса `Recorder`.

        """
        generator = SchemaGenerator.from_json(json_string)
        return cls(generator)
