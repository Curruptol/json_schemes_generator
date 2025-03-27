import json
from typing import Any


class ArrayElementDeduplicator:
    """Удаление дублей в массиве type json схемы"""

    def __init__(self, schema: str | dict):
        if isinstance(schema, str):
            self.schema = json.loads(schema)
            self.schema_input_type = "str"
        elif isinstance(schema, dict):
            self.schema = schema
            self.schema_input_type = "dict"

    def deduplicate_array_of_types(self, element: Any):
        """Рекурсивно обходит каждый объект json схемы в поиске массива type, затем удаляет в нем дубли."""

        if isinstance(element, dict):
            if "type" in element and isinstance(element["type"], list):
                element["type"] = list(dict.fromkeys(element["type"]))

            for key in element:
                self.deduplicate_array_of_types(element=element[key])

    def deduplicate_array_of_types_in_response_scheme(self) -> None | str | dict:
        """
        Вызывает рекурсивное удаление дублей в массиве type для json схемы.

        :return: Если на вход json схема типа str, то вернется схема в str. Если типа dict, то вернется dict.
        """

        self.deduplicate_array_of_types(element=self.schema)

        if self.schema_input_type == "str":
            return json.dumps(self.schema)
        elif self.schema_input_type == "dict":
            return self.schema
