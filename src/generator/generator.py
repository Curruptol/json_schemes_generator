import json
from typing import Any

from src.schema_types.schema_types import Type, ObjectType, ArrayType, NullType, StringType, NumberType, IntegerType
from src.handlers.merge_json_schemes import MergeJSONSchemes
from src.handlers.deduplicate_array_elements import ArrayElementDeduplicator


def json_path(obj, *args):
    """Функция для извлечения значения по пути из JSON-подобного объекта.

    :param obj: Объект, из которого нужно извлечь значение.
    :param args: Путь до нужного значения в виде последовательности ключей.
    :return: Значение по указанному пути или `None`, если путь не существует.

    """
    if not obj:
        return None

    for arg in args:
        if arg not in obj:
            return None
        obj = obj[arg]
    return obj


class SchemaGenerator(object):
    """Класс для генерации схемы JSON-схемы на основе входящего объекта."""

    def __init__(self, base_object):
        """Конструктор класса.

        :param base_object: Базовый объект, на основании которого будет построена схема.

        """
        self._base_object = base_object

    @property
    def base_object(self):
        """Геттер для базового объекта.

        :return: Базовый объект.

        """
        return self._base_object

    @classmethod
    def from_json(cls, base_json: str):
        """Создает экземпляр класса на основе строки JSON.

        :param base_json: Строка JSON, представляющая базовый объект.
        :return: Экземпляр класса `SchemaGenerator`.

        """
        base_object = json.loads(base_json)
        if isinstance(base_object, str):
            try:
                base_object = json.loads(base_object)
            except json.decoder.JSONDecodeError:
                base_object = {}

        obj = cls(base_object)

        return obj

    def to_dict(self,
                base_object: Any = None,
                base_object_name: str = None,
                name_of_element_object: str = None,
                first_level: bool = True,
                options: dict = None) -> dict:
        """Преобразует базовый объект в словарь, соответствующий схеме JSON-схемы.

        :param base_object: Объект, который преобразуется в схему. Если не указан, используется базовый объект.
        :param base_object_name: Наименование объекта.
        :param first_level: Флаг, определяющий, является ли этот уровень первым уровнем рекурсии.
        :param options: Дополнительные параметры для настройки схемы.
        :return: Словарь, представляющий собой JSON-схему.

        """
        if options is None:
            options = {}
        schema_dict = {}

        if first_level:
            base_object = self.base_object
            schema_dict["$schema"] = Type.schema_version
            if "additionalProperties" in options:
                schema_dict["additionalProperties"] = options.get("additionalProperties")

        base_object_type = type(base_object)
        schema_type = Type.get_schema_type_for(base_object_type)

        if schema_type is StringType:
            if "stringMaxLengths" in options:
                for value in options.get("stringMaxLengths"):
                    if value >= len(base_object):
                        schema_dict["maxLength"] = value
                        break
                if len(base_object) > options.get("stringMaxLengths")[-1]:
                    schema_dict["maxLength"] = options.get("stringMaxLengths")[-1]

            if "stringMinLength" in options:
                schema_dict["minLength"] = options.get("stringMinLength")

        if schema_type is IntegerType:
            if "numberMinimum" in options:
                schema_dict["minimum"] = options.get("numberMinimum")
            if "numberMaximum" in options:
                schema_dict["maximum"] = options.get("numberMaximum")

        if schema_type is NumberType:
            if "numberMinimum" in options:
                schema_dict["minimum"] = options.get("numberMinimum")
            if "numberMaximum" in options:
                schema_dict["maximum"] = options.get("numberMaximum")

        if schema_type is NullType:
            schema_dict["type"] = [NullType.json_type]
        else:
            schema_dict["type"] = [schema_type.json_type, NullType.json_type]

        if schema_type is ObjectType:
            schema_dict["properties"] = {}
            if "additionalProperties" in options:
                schema_dict["additionalProperties"] = options.get("additionalProperties")

            for prop, value in base_object.items():
                schema_dict["properties"][prop] = self.to_dict(
                                      base_object=value,
                                      base_object_name=prop,
                                      name_of_element_object=prop if base_object_name is None else base_object_name,
                                      first_level=False,
                                      options=options)

        elif schema_type is ArrayType and len(base_object) > 0:
            if "arrayMaxItems" in options:
                schema_dict["maxItems"] = options.get("arrayMaxItems")
            if "arrayMinItems" in options:
                schema_dict["minItems"] = options.get("arrayMinItems")
            if "additionalItems" in options:
                schema_dict["additionalItems"] = options.get("additionalItems")

            if options.get("enableArray"):
                first_item_type = type(base_object[0])
                same_type = all((type(item) == first_item_type for item in base_object))

                if same_type:
                    schema_dict["items"] = []
                    for idx, item in enumerate(base_object):
                        schema_dict["items"].append(
                            self.to_dict(base_object=item, first_level=False, options=options))

                    merged_items = MergeJSONSchemes.merge_schemes_from_list_str_by_mergedeep(
                        schemas_list=schema_dict["items"])

                    array_element_deduplcator_instance = ArrayElementDeduplicator(schema=merged_items)
                    merged_items = array_element_deduplcator_instance.deduplicate_array_of_types_in_response_scheme()

                    schema_dict["items"].clear()
                    schema_dict["items"].append(merged_items)

                else:
                    schema_dict["items"] = []

                    for idx, item in enumerate(base_object):
                        schema_dict["items"].append(
                            self.to_dict(base_object=item, first_level=False, options=options))

        return schema_dict

    def to_json(self, options: dict) -> str:
        """Преобразует схему в строку JSON.

        :param options: Параметры для настройки схемы.
        :return: Строку JSON, представляющую схему.

        """
        return json.dumps(self.to_dict(options=options))
