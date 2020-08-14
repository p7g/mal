from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import maltypes as t


def pr_str(form: 't.MalType', print_readably: bool = False) -> str:
    import maltypes as t

    if isinstance(form, t.MalSymbol):
        return form.name
    if isinstance(form, t.MalInt):
        return str(form.value)
    if isinstance(form, t.MalString):
        return transform_string(form.value) if print_readably else form.value
    if isinstance(form, t.MalNil):
        return 'nil'
    if isinstance(form, t.MalBool):
        return 'true' if form.value else 'false'
    if isinstance(form, t.MalList):
        return pr_seq(form, '()', print_readably)
    if isinstance(form, t.MalVector):
        return pr_seq(form, '[]', print_readably)
    if isinstance(form, t.MalHashMap):
        return pr_seq(form, '{}', print_readably)
    if isinstance(form, t.MalKeyword):
        return f':{form.name}'
    if isinstance(form, t.MalFunction):
        return f'<function {form.fn.__name__}>'
    raise NotImplementedError(type(form))


def pr_seq(form: 't.MalSequence', delims: str, print_readably: bool) -> str:
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
