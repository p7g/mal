import enum, re
from typing import ClassVar, List, Literal, Final, Type, Union

from malerrors import MalSyntaxError, MalNoInputError
from maltypes import (MalType, MalList, MalAtom, MalInt, MalSymbol, MalNil,
                      MalBool, MalString, MalSequence, MalVector, MalHashMap,
                      MalKeyword)

Token = str
token_re = re.compile(r'[\s,]*(~@|[\[\]{}()\'`~@]'
                      r'|"(?:\\.|[^\\\"])*"?|;.*'
                      r'|[^\s\[\]{}(\'"`,;)]*)')


class _empty(enum.Enum):
    empty = 0


EOF: Final = _empty.empty
_EOF_T = Literal[_empty.empty]


class Reader:
    def __init__(self, tokens: List[Token]):
        self.position = 0
        self.tokens = tokens
        if not tokens:
            raise MalNoInputError()

    def next(self) -> Union[Token, _EOF_T]:
        if self.position >= len(self.tokens):
            return EOF
        tok = self.tokens[self.position]
        self.position += 1
        return tok

    def peek(self) -> Union[Token, _EOF_T]:
        if self.position >= len(self.tokens):
            return EOF
        return self.tokens[self.position]


def read_str(in_: str):
    reader = Reader(tokenize(in_))
    return read_form(reader)


def tokenize(in_: str) -> List[Token]:
    return [t for t in token_re.findall(in_) if t and t[0] != ';']


def read_form(reader: Reader) -> MalType:
    tok = reader.peek()

    if tok == '(':
        return read_seq(reader, '()', MalList)
    if tok == '[':
        return read_seq(reader, '[]', MalVector)
    if tok == '{':
        return read_seq(reader, '{}', MalHashMap)
    return read_atom(reader)


def read_seq(reader: Reader, delims: str, cls: Union[Type[MalSequence],
                                                     Type[MalHashMap]]):
    items = []

    open_, close = tuple(delims)
    assert reader.next() == open_

    while reader.peek() not in (close, EOF):
        items.append(read_form(reader))

    if reader.peek() is EOF:
        raise MalSyntaxError(f'Expected {close}, got EOF')
    else:
        reader.next()

    return cls(items)


def read_atom(reader: Reader) -> MalType:
    tok = reader.next()
    if tok is EOF:
        raise MalSyntaxError('Unexpected EOF')
    if tok[0].isdigit() or (len(tok) > 1 and tok[0] == '-'
                            and tok[1].isdigit()):
        try:
            return MalInt(int(tok))
        except ValueError:
            raise MalSyntaxError(f'Invalid integer literal: {tok}')
    if tok[0] == ':' and len(tok) > 1:
        return MalKeyword(tok[1:])
    if tok == 'nil':
        return MalNil()
    if tok == 'true':
        return MalBool(True)
    if tok == 'false':
        return MalBool(False)
    if tok[0] == '"':
        if len(tok) < 2 or tok[-1] != '"':
            raise MalSyntaxError('Found EOF while parsing string literal')
        return MalString(transform_string(tok[1:-1]))
    if tok in ("'", '`', '~', '~@', '@'):
        return MalList([
            MalSymbol({
                "'": 'quote',
                '`': 'quasiquote',
                '~': 'unquote',
                '~@': 'splice-unquote',
                '@': 'deref',
            }[tok]),
            read_form(reader)
        ])
    if tok == '^':
        meta = read_form(reader)
        form = read_form(reader)
        return MalList([MalSymbol('with-meta'), form, meta])
    return MalSymbol(tok)


def transform_string(in_: str) -> str:
    output = []
    it = (c for c in in_)

    for c in it:
        if c != '\\':
            output.append(c)
            continue
        try:
            c = next(it)
        except StopIteration:
            raise MalSyntaxError('Unexpected EOF in string literal')
        if c not in '"n\\':
            raise MalSyntaxError('Invalid escape sequence')
        output.append({'n': '\n'}.get(c, c))

    return ''.join(output)
