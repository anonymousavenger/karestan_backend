import json
import re
from enum import Enum

def cap_to_kebab(name):
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', name).lower()


def pluralize(name:str):
    if name.endswith('y'):
        return name[0:-1] + 'ies'
    else:
        return name + 's'

class BaseEnum(str,Enum):

    def __str__(self) -> str:
        return str(self.name)

    def to_dict(self):
        return {self.name: self.value}

    @classmethod
    def map_all(cls) -> dict:
        return {name: enum.value for name, enum in cls.__members__.items()}

    @classmethod
    def names(cls) -> list:
        return [name for name in cls.__members__.keys()]