try:
    import readline
except ImportError:
    pass


def READ(a: str):
    return a


def EVAL(a: str):
    return a


def PRINT(a: str):
    return a


def rep(in_: str):
    return PRINT(EVAL(READ(in_)))


if __name__ == '__main__':
    try:
        while True:
            print(rep(input('user> ')))
    except EOFError:
        print()
