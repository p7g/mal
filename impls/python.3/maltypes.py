from typing import List, Tuple

from malerrors import MalSyntaxError


class MalType:
    pass


class MalSequence(MalType):
    items: List[MalType]

    def __init__(self, items: List[MalType]):
        self.items = items


class MalList(MalSequence):
    pass


class MalVector(MalSequence):
    pass


class MalHashMap(MalSequence):
    def __init__(self, items: List[MalType]):
        num_items = len(items)
        if num_items % 2 != 0:
            raise MalSyntaxError('Expected even number of items in hash map')
        super().__init__(items)


class MalAtom(MalType):
    pass


class MalKeyword(MalAtom):
    name: str

    def __init__(self, name: str):
        self.name = name


class MalInt(MalAtom):
    value: int

    def __init__(self, value: int):
        self.value = value


class MalSymbol(MalAtom):
    name: str

    def __init__(self, name: str):
        self.name = name


class MalBool(MalAtom):
    value: bool

    def __init__(self, value: bool):
        self.value = value


class MalNil(MalAtom):
    pass


class MalString(MalAtom):
    value: str

    def __init__(self, value: str):
        self.value = value
