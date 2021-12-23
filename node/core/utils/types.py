from enum import IntEnum, unique
from typing import NamedTuple

from pydantic import conint, constr
from pydantic.types import _registered

# TODO(dmu) MEDIUM: Move business logic related types to `node.blockchain.types`


@unique
class Type(IntEnum):
    GENESIS = 0
    NODE_DECLARATION = 1


@unique
class NodeRole(IntEnum):
    PRIMARY_VALIDATOR = 1
    CONFIRMATION_VALIDATOR = 2
    REGULAR_NODE = 3


hexstr = constr(regex=r'^[0-9a-f]+$', strict=True)
hexstr_i = constr(regex=r'^[0-9a-fA-F]+$', strict=True)  # case-insensitive hexstr

intstr = constr(regex=r'^(?:0|[1-9][0-9]*)$', strict=True)
positive_int = conint(ge=0, strict=True)


class hexstr64(hexstr):  # type: ignore
    min_length = 64
    max_length = 64


class hexstr64_i(hexstr_i):  # type: ignore
    min_length = 64
    max_length = 64


class hexstr128(hexstr):  # type: ignore
    min_length = 128
    max_length = 128


@_registered
class AccountNumber(hexstr64):
    pass


@_registered
class AlphaAccountNumber(hexstr64_i, AccountNumber):
    pass


@_registered
class Hash(hexstr64):
    pass


@_registered
class AccountLock(Hash):
    pass


@_registered
class AlphaAccountLock(hexstr64_i, AccountLock):
    pass


@_registered
class BlockIdentifier(Hash):
    pass


@_registered
class SigningKey(hexstr64):
    pass


@_registered
class Signature(hexstr128):
    pass


class KeyPair(NamedTuple):
    public: AccountNumber
    private: SigningKey
