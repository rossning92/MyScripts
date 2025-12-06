from typing import Any, Dict, List, Literal, NotRequired, TypedDict, cast


class _ArrayType(TypedDict):
    type: Literal["array"]
    items: "JSONSchema"


class _ObjectType(TypedDict):
    type: Literal["object"]
    properties: Dict[str, "JSONSchema"]
    required: NotRequired[List[str]]


class _PrimitiveType(TypedDict):
    type: Literal["integer", "number", "boolean"]


class _StringType(TypedDict):
    type: Literal["string"]
    enum: NotRequired[List[str]]


JSONSchema = _PrimitiveType | _StringType | _ArrayType | _ObjectType


def jsonschema_to_python_type(schema: JSONSchema) -> Any:
    if schema["type"] == "string":
        return str
    elif schema["type"] == "number":
        return float
    elif schema["type"] == "integer":
        return int
    elif schema["type"] == "boolean":
        return bool
    elif schema["type"] == "array":
        return [jsonschema_to_python_type(schema["items"])]
    elif schema["type"] == "object":
        object_schema = cast(_ObjectType, schema)
        props = object_schema.get("properties", {})
        return {key: jsonschema_to_python_type(value) for key, value in props.items()}
    else:
        schema_type = schema["type"]
        raise ValueError(f"Unsupported JSON schema type: {schema_type}")
