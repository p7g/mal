try:
    import readline
except ImportError:
    pass

import functools
import operator as o
from typing import cast, Callable, ChainMap, Dict, List, Tuple

import maltypes as t
from malerrors import MalError, MalNoInputError
from reader import read_str
from printer import pr_str

Env = ChainMap[str, t.MalType]


def _int_op(op: Callable[[int, int], int]) -> t.MalFunction:
    @functools.wraps(op)
    def wrapper(*args: t.MalType) -> t.MalType:
        if not all(isinstance(i, t.MalInt) for i in args):
            raise MalError('Only ints are supported as arguments')
        acc, *rest = map(o.attrgetter('value'),
                         args)  # type: Tuple[int, List[int]]
        for i in rest:
            acc = op(acc, i)
        return t.MalInt(acc)

    return t.MalFunction(cast(t.MalNativeFunction, wrapper))


repl_env: Env = ChainMap({
    '+': _int_op(o.add),
    '-': _int_op(o.sub),
    '*': _int_op(o.mul),
    '/': _int_op(o.floordiv),
})


def READ(in_: str) -> t.MalType:
    return read_str(in_)


def eval_ast(ast: t.MalType, env: Env) -> t.MalType:
    if isinstance(ast, t.MalSymbol):
        try:
            return env[ast.name]
        except KeyError:
            raise MalError(f'{ast.name} not found')
    if isinstance(ast, (t.MalList, t.MalVector)):
        return type(ast)([EVAL(i, env) for i in ast.items])
    if isinstance(ast, t.MalHashMap):
        items = []
        for k, v in ast.items.items():
            items.append(k)
            items.append(EVAL(v, env))
        return t.MalHashMap(items)
    return ast


def EVAL(in_: t.MalType, env: Env) -> t.MalType:
    if not isinstance(in_, t.MalList):
        return eval_ast(in_, env)
    if not in_.items:
        return in_
    f, *args = in_.items
    if isinstance(f, t.MalSymbol):
        if f.name == 'def!':
            if len(args) != 2:
                raise MalError('Expected 2 arguments to "def!"')
            dest, val = args
            if not isinstance(dest, t.MalSymbol):
                raise MalError('Expected symbol name to "def!"')
            res = env[dest.name] = EVAL(val, env)
            return res
        elif f.name == 'let*':
            if len(args) != 2:
                raise MalError('Expected 2 arguments to "let*"')
            new_env = env.new_child()
            bindings, body = args
            if (not isinstance(bindings, (t.MalVector, t.MalList))
                    or len(bindings.items) % 2 != 0):
                raise MalError('Expected let* bindings to be even length list')
            for i in range(0, len(bindings.items) // 2 + 1, 2):
                name, value = bindings.items[i:i + 2]
                if not isinstance(name, t.MalSymbol):
                    raise MalError('Expected symbol name in let* binding')
                new_env[name.name] = EVAL(value, new_env)
            return EVAL(body, new_env)
    f, *args = cast(t.MalList, eval_ast(in_, env)).items
    if isinstance(f, t.MalFunction):
        return f.fn(*args)
    raise MalError(f'Value {pr_str(f)} is not callable')


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
