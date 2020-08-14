try:
    import readline
except ImportError:
    pass

from malerrors import MalError, MalNoInputError
from reader import read_str
from maltypes import MalType
from printer import pr_str


def READ(in_: str) -> MalType:
    return read_str(in_)


def EVAL(in_: MalType) -> MalType:
    return in_


def PRINT(in_: MalType) -> str:
    return pr_str(in_, print_readably=True)


def rep(in_: str):
    return PRINT(EVAL(READ(in_)))


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
