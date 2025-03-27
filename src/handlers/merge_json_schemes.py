import json
from jsonmerge import merge
from mergedeep import merge, Strategy


class MergeJSONSchemes:

    @staticmethod
    def merge_schemes_by_jsonmerge(schemes: list[str | dict]) -> str | dict:
        element_type_in_list = ""

        for element in schemes:
            if isinstance(element, str):
                element_type_in_list = "str"
            elif isinstance(element, dict):
                element_type_in_list = "dict"
            else:
                raise TypeError

        merged_schemes = {}

        for schema in schemes:
            if element_type_in_list == "str":
                schema = json.loads(schema)
            merged_schemes = merge(merged_schemes, schema)

        if element_type_in_list == "str":
            return json.dumps(merged_schemes)
        else:
            return merged_schemes

    @staticmethod
    def merge_schemes_from_list_str_by_mergedeep(schemas_list: list[str | dict]) -> str | dict:
        """Объединение нескольких JSON схем в одну.

        :param schemas_list: Список JSON схем.
        :return: Объединённая JSON схема.

        """
        element_type_in_list = ""

        for element in schemas_list:
            if isinstance(element, str):
                element_type_in_list = "str"
            elif isinstance(element, dict):
                element_type_in_list = "dict"
            else:
                raise TypeError

        merged_schema_dict = {}

        for schema in schemas_list:
            if element_type_in_list == "str":
                schema = json.loads(schema)

            merged_schema_dict = merge({}, merged_schema_dict, schema, strategy=Strategy.ADDITIVE)

        if element_type_in_list == "str":
            return json.dumps(merged_schema_dict)
        elif element_type_in_list == "dict":
            return merged_schema_dict
