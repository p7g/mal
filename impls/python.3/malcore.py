import functools
import operator as o
from os.path import dirname
from typing import cast, Callable, Dict, Iterable, List, Tuple, TypeVar

import maltypes as t
from malerrors import MalError
from printer import pr_str


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
    **cmp_fns,
}


def init(rep: Callable[[str], None]):
    with open(f'{dirname(__file__)}/core.mal', 'r') as f:
        core_str = f.read()

    rep(f'(do {core_str})')
