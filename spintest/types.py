"""Allow computed value to have types."""

import jinja2
import json


class JSONValue(object):
    """A base class that implements type-aware serialization values."""

    def __init__(self, value):
        self.value = value

    def get_value(self, output):
        template = jinja2.Template(self.value)
        return template.render(**output)

    def serialize(self, output):
        return self.get_value(output)


class Int(JSONValue):
    """Converts value to `int`."""

    def serialize(self, output):
        return int(self.get_value(output))


class List(JSONValue):
    """Converts value to `list`."""

    def serialize(self, output):
        return list(self.get_value(output))


class Float(JSONValue):
    """Converts value to `float`."""

    def serialize(self, output):
        return float(self.get_value(output))


class Bool(JSONValue):
    """Converts value to `bool`."""

    def serialize(self, output):
        return bool(self.get_value(output))


class TypeAwareEncoder(json.JSONEncoder):

    output = None

    def default(self, obj):
        if isinstance(obj, JSONValue):
            return obj.serialize(self.output)
        return json.JSONEncoder.default(self, obj)


def type_aware_encoder(output):
    TypeAwareEncoder.output = output
    return TypeAwareEncoder
