try:
    from typing import Final, Literal, Protocol
except ImportError:
    from typing_extensions import Final, Literal, Protocol  # type: ignore


__all__ = ('Final', 'Literal', 'Protocol')
