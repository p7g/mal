from typing import TYPE_CHECKING

from maltypes import (MalType, MalList, MalInt, MalSymbol, MalBool, MalNil,
                      MalString, MalSequence, MalVector, MalHashMap,
                      MalKeyword)


def pr_str(form: MalType, print_readably: bool = False) -> str:
    if isinstance(form, MalSymbol):
        return form.name
    if isinstance(form, MalInt):
        return str(form.value)
    if isinstance(form, MalString):
        return transform_string(form.value) if print_readably else form.value
    if isinstance(form, MalNil):
        return 'nil'
    if isinstance(form, MalBool):
        return 'true' if form.value else 'false'
    if isinstance(form, MalList):
        return pr_seq(form, '()', print_readably)
    if isinstance(form, MalVector):
        return pr_seq(form, '[]', print_readably)
    if isinstance(form, MalHashMap):
        return pr_seq(form, '{}', print_readably)
    if isinstance(form, MalKeyword):
        return f':{form.name}'
    raise NotImplementedError(type(form))


def pr_seq(form: MalSequence, delims: str, print_readably: bool) -> str:
    open_, close = tuple(delims)
    inner = ' '.join([pr_str(f, print_readably) for f in form.items])
    return f'{open_}{inner}{close}'


def transform_string(in_: str) -> str:
    replacements = {
        '"': '\\"',
        '\n': '\\n',
        '\\': '\\\\',
    }
    content = ''.join([replacements.get(c, c) for c in in_])
    return f'"{content}"'
