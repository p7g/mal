from abc import ABC, abstractmethod
from functools import total_ordering
from itertools import tee
from typing import Callable, Dict, List, Protocol, Tuple

from malerrors import MalSyntaxError
from printer import pr_str


class MalType(ABC):
    @abstractmethod
    def __hash__(self) -> int:
        ...

    def __eq__(self, other):
        return type(self) is type(other) and hash(self) == hash(other)

    __str__ = pr_str

    def is_truthy(self) -> bool:
        return True


class MalSequence(MalType, ABC):
    items: List[MalType]

    def __init__(self, items: List[MalType]):
        self.items = items

    def __hash__(self):
        return hash(('MalSequence', tuple(self.items)))

    def __eq__(self, other):
        return isinstance(other, MalSequence) and hash(self) == hash(other)


class MalList(MalSequence):
    pass


class MalVector(MalSequence):
    pass


class MalHashMap(MalType):
    items: Dict[MalType, MalType]

    def __init__(self, items: List[MalType]):
        num_items = len(items)
        if num_items % 2 != 0:
            raise MalSyntaxError('Expected even number of items in hash map')
        self.items = {}
        for i in range(0, num_items, 2):
            self.items[items[i]] = items[i + 1]

    def __hash__(self):
        return hash((type(self).__name__, tuple(self.items)))


class MalAtom(MalType, ABC):
    pass


class MalKeyword(MalAtom):
    name: str

    def __init__(self, name: str):
        self.name = name

    def __hash__(self):
        return hash(self.name)


@total_ordering
class MalInt(MalAtom):
    value: int

    def __init__(self, value: int):
        self.value = value

    def __hash__(self):
        return hash(self.value)

    def __lt__(self, other):
        if not isinstance(other, MalInt):
            return NotImplemented
        return self.value < other.value


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

    def is_truthy(self):
        return self.value


class MalNil(MalAtom):
    def __hash__(self):
        return hash(None)

    def is_truthy(self):
        return False


class MalString(MalAtom):
    value: str

    def __init__(self, value: str):
        self.value = value

    def __hash__(self):
        return hash(self.value)


class MalNativeFunction(Protocol):
    def __call__(self, *args: MalType) -> MalType:
        ...


class MalFunction(MalType):
    fn: MalNativeFunction

    def __init__(self, fn: MalNativeFunction):
        self.fn = fn

    def __hash__(self):
        return hash(self.fn)
