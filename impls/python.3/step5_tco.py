try:
    import readline
except ImportError:
    pass

from typing import cast, ChainMap, Dict, List, Sequence

import malcore as core
import maltypes as t
from malerrors import MalError, MalNoInputError, MalSyntaxError
from malenv import Env
from reader import read_str
from printer import pr_str

repl_env: Env = Env(core.ns)


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
    while True:
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

            if f.name == 'let*':
                if len(args) != 2:
                    raise MalError('Expected 2 arguments to "let*"')
                new_env = env.new_child()
                bindings, body = args
                if (not isinstance(bindings, (t.MalVector, t.MalList))
                        or len(bindings.items) % 2 != 0):
                    raise MalError(
                        'Expected let* bindings to be even length list')
                for i in range(0, len(bindings.items) // 2 + 1, 2):
                    name, value = bindings.items[i:i + 2]
                    if not isinstance(name, t.MalSymbol):
                        raise MalError('Expected symbol name in let* binding')
                    new_env[name.name] = EVAL(value, new_env)
                env = new_env
                in_ = body
                continue

            if f.name == 'do':
                if not args:
                    raise MalError('Expected body in do expr')
                eval_ast(t.MalList(args[:-1]), env)
                in_ = args[-1]
                continue

            if f.name == 'if':
                if len(args) not in (2, 3):
                    raise MalError('Expected 2 or 3 arguments to if')
                cond, then, *else_ = args
                if EVAL(cond, env).is_truthy():
                    in_ = then
                elif else_:
                    in_ = else_[0]
                else:
                    in_ = t.MalNil()
                continue

            if f.name == 'fn*':
                if len(args) != 2:
                    raise MalError('Expected 2 arguments to fn*')
                params, body = args
                if not isinstance(params, (t.MalList, t.MalVector)):
                    raise MalError('Parameters must be list or vector')
                if not all(isinstance(p, t.MalSymbol) for p in params.items):
                    raise MalError('Parameters must be symbols')
                return t.MalTCOFunction(
                    ast=body,
                    params=params,
                    env=env,
                    fn=t.MalFunction(
                        _make_closure(
                            env,
                            [cast(t.MalSymbol, p).name
                             for p in params.items], body)),
                )
        f, *args = cast(t.MalList, eval_ast(in_, env)).items
        if isinstance(f, t.MalFunction):
            return f.fn(*args)
        if isinstance(f, t.MalTCOFunction):
            in_ = f.ast
            binds = [
                cast(t.MalSymbol, p).name
                for p in cast(t.MalSequence, f.params).items
            ]
            env = f.env.new_child(_make_fn_bindings(binds, list(args)))
            continue
        raise MalError(f'Value {pr_str(f)} is not callable')


def _make_fn_bindings(binds: List[str],
                      args: List[t.MalType]) -> Dict[str, t.MalType]:
    try:
        rest_index = binds.index('&')
    except ValueError:
        rest_index = -1

    if rest_index != -1:
        if len(binds) > rest_index + 2:
            raise MalSyntaxError('Can only have one rest parameter')
        binds.pop(rest_index)
        args.insert(rest_index, t.MalList(args[rest_index:]))

    return dict(zip(binds, args))


def _make_closure(env: Env, binds: List[str],
                  body: t.MalType) -> t.MalNativeFunction:
    def closure(*args: t.MalType) -> t.MalType:
        new_env = env.new_child(_make_fn_bindings(binds, list(args)))
        return EVAL(body, new_env)

    return closure


def PRINT(in_: t.MalType) -> str:
    return pr_str(in_, print_readably=True)


def rep(in_: str):
    return PRINT(EVAL(READ(in_), repl_env))


if __name__ == '__main__':
    core.init(rep)

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
