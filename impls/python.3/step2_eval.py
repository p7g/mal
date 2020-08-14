try:
    import readline
except ImportError:
    pass

import functools
import operator as o
from typing import Callable, Dict, List, Tuple

import maltypes as t
from malerrors import MalError, MalNoInputError
from reader import read_str
from printer import pr_str

Env = Dict[str, Callable[[t.MalType, t.MalType], t.MalType]]


def _int_op(
    op: Callable[[int, int],
                 int]) -> Callable[[t.MalType, t.MalType], t.MalType]:
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


repl_env: Env = {
    '+': _int_op(o.add),
    '-': _int_op(o.sub),
    '*': _int_op(o.mul),
    '/': _int_op(o.floordiv),
}


def READ(in_: str) -> t.MalType:
    return read_str(in_)


def eval_ast(ast: t.MalType, env: Env):
    if isinstance(ast, t.MalSymbol):
        if ast.name in env:
            return env[ast.name]
        raise MalError(f'Unbound symbol {ast.name}')
    if isinstance(ast, (t.MalList, t.MalVector)):
        return type(ast)([EVAL(i, env) for i in ast.items])
    if isinstance(ast, t.MalHashMap):
        return t.MalHashMap([
            EVAL(item, env) if i % 2 == 1 else item
            for i, item in enumerate(ast.items)
        ])
    return ast


def EVAL(in_: t.MalType, env: Env) -> t.MalType:
    if not isinstance(in_, t.MalList):
        return eval_ast(in_, env)
    if not in_.items:
        return in_
    f, *args = eval_ast(in_, env).items
    return f(*args)


def PRINT(in_: t.MalType) -> str:
    return pr_str(in_, print_readably=True)


def rep(in_: str):
    return PRINT(EVAL(READ(in_), repl_env))


if __name__ == '__main__':
    while True:
        try:
            print(rep(input('user> ')))
        except EOFError:
            print()
            break
        except MalNoInputError:
            continue
        except MalError as e:
            import sys

            print(str(e), file=sys.stderr)
