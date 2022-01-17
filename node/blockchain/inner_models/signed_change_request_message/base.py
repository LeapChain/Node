from node.blockchain.inner_models.base import BaseModel
from node.blockchain.mixins.crypto import SignableMixin
from node.blockchain.types import AccountLock, Type


class SignedChangeRequestMessage(BaseModel, SignableMixin):
    account_lock: AccountLock
    type: Type  # noqa: A003
