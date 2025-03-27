from typing import Any

from src.configs.config import config_json


class Type(object):
    schema_version = config_json.get("VARIABLES").get("json_schema_options").get("schemaVersion")
    json_type = None
    id = None
    required = False

    @classmethod
    def get_schema_type_for(self, t: Any):
        """
        получение типа элемента для схемы
        :param t:
        :return:
        """

        schema_type = SCHEMA_TYPES.get(t)

        if not schema_type:
            raise JsonSchemaTypeNotFound(
                "There is no schema type for %s.\n Try:\n %s" % (
                    str(t), ",\n".join(["\t%s" % str(k) for k in SCHEMA_TYPES.keys()])
                )
            )

        return schema_type


class NumberType(object):
    json_type = "number"


class IntegerType(object):
    json_type = "integer"


class StringType(object):
    json_type = "string"


class NullType(object):
    json_type = "null"


class BooleanType(object):
    json_type = "boolean"


class ArrayType(object):
    json_type = "array"
    items = []


class ObjectType(object):
    json_type = "object"
    properties = {}


class JsonSchemaTypeNotFound(Exception):
    pass

SCHEMA_TYPES = {
    type(None): NullType,
    str: StringType,
    int: IntegerType,
    float: NumberType,
    bool: BooleanType,
    list: ArrayType,
    dict: ObjectType,
}
