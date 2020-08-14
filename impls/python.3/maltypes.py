from abc import ABC, abstractmethod
from typing import Callable, List, Protocol, Tuple

from malerrors import MalSyntaxError
from printer import pr_str


class MalType(ABC):
    @abstractmethod
    def __hash__(self) -> int:
        ...

    def __eq__(self, other):
        return type(self) is type(other) and hash(self) == hash(other)

    __str__ = pr_str


class MalSequence(MalType, ABC):
    items: List[MalType]

    def __init__(self, items: List[MalType]):
        self.items = items

    def __hash__(self):
        return hash((type(self).__hash__, tuple(self.items)))


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


class MalAtom(MalType, ABC):
    pass


class MalKeyword(MalAtom):
    name: str

    def __init__(self, name: str):
        self.name = name

    def __hash__(self):
        return hash(self.name)


class MalInt(MalAtom):
    value: int

    def __init__(self, value: int):
        self.value = value

    def __hash__(self):
        return hash(self.value)


class MalSymbol(MalAtom):
    name: str

    def __init__(self, name: str):
        self.name = name

    def __hash__(self):
        return hash((type(self).__name__, self.name))


class MalBool(MalAtom):
    value: bool

    def __init__(self, value: bool):
        self.value = value

    def __hash__(self):
        return hash(self.value)


class MalNil(MalAtom):
    def __hash__(self):
        return hash(None)


class MalString(MalAtom):
    value: str

    def __init__(self, value: str):
        self.value = value

    def __hash__(self):
        return hash(self.value)


class MalNativeFunction(Protocol):
    __name__: str

    def __call__(self, *args: MalType) -> MalType:
        ...


class MalFunction(MalType):
    fn: MalNativeFunction

    def __init__(self, fn: MalNativeFunction):
        self.fn = fn

    def __hash__(self):
        return hash(self.fn)
