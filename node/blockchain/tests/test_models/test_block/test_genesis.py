import pytest

from node.blockchain.inner_models import BlockMessage
from node.blockchain.models.block import Block
from node.core.utils.cryptography import is_signature_valid
from node.core.utils.types import Signature, Type


@pytest.mark.django_db
def test_create_from_block_message(genesis_block_message, primary_validator_key_pair):
    block = Block.objects.add_block_from_block_message(
        message=genesis_block_message,
        signing_key=primary_validator_key_pair.private,
        validate=False,
    )
    assert block.signer == primary_validator_key_pair.public
    assert isinstance(block.message, str)
    assert isinstance(block.signature, str)
    assert is_signature_valid(block.signer, block.message.encode('utf-8'), Signature(block.signature))
    message = BlockMessage.parse_raw(block.message)
    assert message.number == 0
    assert message.identifier is None
    assert message.type == Type.GENESIS
    assert message == genesis_block_message

    block = Block.objects.get(_id=0)
    assert block.signer == primary_validator_key_pair.public
    assert isinstance(block.message, str)
    assert isinstance(block.signature, str)
    assert is_signature_valid(block.signer, block.message.encode('utf-8'), Signature(block.signature))
    message = BlockMessage.parse_raw(block.message)
    assert message.number == 0
    assert message.identifier is None
    assert message.type == Type.GENESIS
    assert message == genesis_block_message
