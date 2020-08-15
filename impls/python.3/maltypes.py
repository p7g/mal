from abc import ABC, abstractmethod
from functools import total_ordering
from typing import TYPE_CHECKING, Dict, List, Protocol

from malerrors import MalSyntaxError
from printer import pr_str

if TYPE_CHECKING:
    from malenv import Env


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


class MalAtom(MalType):
    inner: MalType

    def __init__(self, inner: MalType):
        self.inner = inner

    def __hash__(self):
        return hash((type(self).__name__, hash(id(self))))


class MalKeyword(MalType):
    name: str

    def __init__(self, name: str):
        self.name = name

    def __hash__(self):
        return hash(self.name)


@total_ordering
class MalInt(MalType):
    value: int

    def __init__(self, value: int):
        self.value = value

    def __hash__(self):
        return hash(self.value)

    def __lt__(self, other):
        if not isinstance(other, MalInt):
            return NotImplemented
        return self.value < other.value


class MalSymbol(MalType):
    name: str

    def __init__(self, name: str):
        self.name = name

    def __hash__(self):
        return hash((type(self).__name__, self.name))


class MalBool(MalType):
    value: bool

    def __init__(self, value: bool):
        self.value = value

    def __hash__(self):
        return hash(self.value)

    def is_truthy(self):
        return self.value


class MalNil(MalType):
    def __hash__(self):
        return hash(None)

    def is_truthy(self):
        return False


class MalString(MalType):
    value: str

    def __init__(self, value: str):
        self.value = value

    def __hash__(self):
        return hash(self.value)


class MalCallable(MalType, ABC):
    pass


class MalNativeFunction(Protocol):
    def __call__(self, *args: MalType) -> MalType:
        ...


class MalFunction(MalCallable):
    fn: MalNativeFunction

    def __init__(self, fn: MalNativeFunction):
        self.fn = fn

    def __hash__(self):
        return hash(self.fn)


class MalTCOFunction(MalCallable):
    ast: MalType
    params: MalType
    env: 'Env'
    fn: MalFunction

    def __init__(self, ast: MalType, params: MalType, env: 'Env',
                 fn: MalFunction):
        self.ast = ast
        self.params = params
        self.env = env
        self.fn = fn

    def __hash__(self):
        return hash(self.fn)
