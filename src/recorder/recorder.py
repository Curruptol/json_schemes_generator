from src.generator.generator import SchemaGenerator


class Recorder(object):
    """Записс и сохранения JSON-схем."""

    def __init__(self, generator: SchemaGenerator):
        self.generator = generator

    @classmethod
    def from_str(cls, json_string: str):
        """
        Создает экземпляр класса на основе строки JSON.

        :param json_string: Строка JSON.
        :return: Экземпляр класса `Recorder`.
        """

        generator = SchemaGenerator.from_json(json_string)
        return cls(generator)
