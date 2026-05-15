import sys
import types
from unittest.mock import MagicMock


def install_if_missing():
    if "boto3" in sys.modules:
        return sys.modules["boto3"]

    boto3 = types.ModuleType("boto3")
    boto3.resource = MagicMock()
    boto3.client = MagicMock()

    dynamodb = types.ModuleType("boto3.dynamodb")
    conditions = types.ModuleType("boto3.dynamodb.conditions")

    class Key:
        def __init__(self, name):
            self.name = name

        def eq(self, value):
            return ("eq", self.name, value)

    conditions.Key = Key
    dynamodb.conditions = conditions

    sys.modules["boto3"] = boto3
    sys.modules["boto3.dynamodb"] = dynamodb
    sys.modules["boto3.dynamodb.conditions"] = conditions

    return boto3
