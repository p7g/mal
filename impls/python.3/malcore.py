import functools
import operator as o
from os.path import dirname
from typing import (TYPE_CHECKING, Callable, Dict, Iterable, List, Tuple,
                    TypeVar)

import maltypes as t
from malerrors import MalError
from printer import pr_str
from reader import read_str

if TYPE_CHECKING:
    from malenv import Env  # noqa


def malfn(fn: t.MalNativeFunction) -> t.MalFunction:
    return t.MalFunction(fn)


def _int_op(op: Callable[[int, int], int]) -> t.MalFunction:
    @malfn
    @functools.wraps(op)
    def wrapper(*args: t.MalType) -> t.MalType:
        if not all(isinstance(i, t.MalInt) for i in args):
            raise MalError('Only ints are supported as arguments')
        acc, *rest = map(o.attrgetter('value'),
                         args)  # type: Tuple[int, List[int]]
        for i in rest:
            acc = op(acc, i)
        return t.MalInt(acc)

    return wrapper


@malfn
def list_(*args: t.MalType) -> t.MalType:
    return t.MalList(list(args))


@malfn
def list_p(*args: t.MalType) -> t.MalType:
    if len(args) != 1:
        raise MalError(f'Expected 1 argument to list?, got {len(args)}')
    return t.MalBool(isinstance(args[0], t.MalList))


@malfn
def empty_p(*args: t.MalType) -> t.MalType:
    if len(args) != 1 or not isinstance(args[0], t.MalSequence):
        raise MalError('Expected argument to empty? to be sequence')
    return t.MalBool(len(args[0].items) == 0)


@malfn
def count(*args: t.MalType) -> t.MalType:
    if len(args) != 1 or not isinstance(args[0], (t.MalSequence, t.MalNil)):
        raise MalError('Expected argument to count to be sequence')
    if isinstance(args[0], t.MalNil):
        return t.MalInt(0)
    return t.MalInt(len(args[0].items))


@malfn
def pr_str_(*args: t.MalType) -> t.MalType:
    return t.MalString(' '.join([pr_str(a, print_readably=True)
                                 for a in args]))


@malfn
def str_(*args: t.MalType) -> t.MalType:
    return t.MalString(''.join(map(pr_str, args)))


@malfn
def prn(*args: t.MalType) -> t.MalType:
    print(' '.join([pr_str(a, print_readably=True) for a in args]))
    return t.MalNil()


@malfn
def println(*args: t.MalType) -> t.MalType:
    print(' '.join(map(pr_str, args)))
    return t.MalNil()


@malfn
def read_string(*args: t.MalType) -> t.MalType:
    if len(args) != 1 or not isinstance(args[0], t.MalString):
        raise MalError('Expected read-string arg to be string')
    return read_str(args[0].value)


@malfn
def slurp(*args: t.MalType) -> t.MalType:
    if len(args) != 1 or not isinstance(args[0], t.MalString):
        raise MalError('Expected slurp arg to be string')
    try:
        with open(args[0].value, 'r') as f:
            return t.MalString(f.read())
    except FileNotFoundError:
        raise MalError(f'File {args[0].value} does not exist')
    except OSError:
        raise MalError(f'Failed to read file {args[0].value}')


@malfn
def atom(*args: t.MalType) -> t.MalType:
    if len(args) != 1:
        raise MalError('Expected one argument to atom')
    return t.MalAtom(args[0])


@malfn
def atom_p(*args: t.MalType) -> t.MalType:
    if len(args) != 1:
        raise MalError('Expected one argument to atom?')
    return t.MalBool(isinstance(args[0], t.MalAtom))


@malfn
def deref(*args: t.MalType) -> t.MalType:
    if len(args) != 1 or not isinstance(args[0], t.MalAtom):
        raise MalError('Expected deref argument to be atom')
    return args[0].inner


@malfn
def reset(*args: t.MalType) -> t.MalType:
    if len(args) != 2 or not isinstance(args[0], t.MalAtom):
        raise MalError('Expected atom and value as arguments to reset!')
    args[0].inner = args[1]
    return args[1]


@malfn
def swap(*args: t.MalType) -> t.MalType:
    if (len(args) < 2 or not isinstance(args[0], t.MalAtom)
            or not isinstance(args[1], t.MalCallable)):
        raise MalError('Expected atom and function as arguments to swap!')
    atom, callable_, *rest = args
    assert isinstance(atom, t.MalAtom) and isinstance(callable_, t.MalCallable)
    if isinstance(callable_, t.MalTCOFunction):
        callable_ = callable_.fn
    assert isinstance(callable_, t.MalFunction), 'Unsupported callable'
    new_value = atom.inner = callable_.fn(atom.inner, *rest)
    return new_value


pairwise_T = TypeVar('pairwise_T')


def _pairwise(
        it: Iterable[pairwise_T]) -> Iterable[Tuple[pairwise_T, pairwise_T]]:
    from itertools import tee

    a, b = tee(it)
    next(b, None)
    return zip(a, b)


def _mkcmp(op) -> t.MalFunction:
    @malfn
    def _cmp_fn(*args: t.MalType) -> t.MalType:
        try:
            return t.MalBool(all(op(a, b) for a, b in _pairwise(args)))
        except TypeError:
            types = ', '.join([type(v).__name__ for v in args])
            raise MalError(f'Cannot compare values of types {types}')

    return _cmp_fn


cmp_fns = dict((name, _mkcmp(op)) for name, op in [
    ('=', o.eq),
    ('<', o.lt),
    ('<=', lambda a, b: not o.gt(a, b)),
    ('>', o.gt),
    ('>=', lambda a, b: not o.lt(a, b)),
])

ns: Dict[str, t.MalFunction] = {
    '+': _int_op(o.add),
    '-': _int_op(o.sub),
    '*': _int_op(o.mul),
    '/': _int_op(o.floordiv),
    'prn': prn,
    'list': list_,
    'list?': list_p,
    'count': count,
    'empty?': empty_p,
    'pr-str': pr_str_,
    'str': str_,
    'println': println,
    'read-string': read_string,
    'slurp': slurp,
    'atom': atom,
    'atom?': atom_p,
    'deref': deref,
    'reset!': reset,
    'swap!': swap,
    **cmp_fns,
}


def make_eval(EVAL: Callable[[t.MalType], t.MalType]) -> t.MalFunction:
    @malfn
    def evil(*args: t.MalType) -> t.MalType:
        if len(args) != 1:
            raise MalError('Expected one argument to eval')
        return EVAL(args[0])

    return evil


def init(rep: Callable[[str], None]):
    with open(f'{dirname(__file__)}/core.mal', 'r') as f:
        core_str = f.read()

    rep(f'(do {core_str})')
