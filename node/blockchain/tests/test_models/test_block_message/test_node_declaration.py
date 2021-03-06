import json
import re
from datetime import datetime

import pytest
from pydantic import ValidationError

from node.blockchain.facade import BlockchainFacade
from node.blockchain.inner_models import (
    AccountState, BlockMessage, BlockMessageUpdate, NodeDeclarationBlockMessage, NodeDeclarationSignedChangeRequest
)
from node.blockchain.types import Type


@pytest.mark.usefixtures('base_blockchain')
def test_create_from_signed_change_request(
    node_declaration_signed_change_request_message, regular_node_key_pair, regular_node
):
    request = NodeDeclarationSignedChangeRequest.create_from_signed_change_request_message(
        message=node_declaration_signed_change_request_message,
        signing_key=regular_node_key_pair.private,
    )
    blockchain_facade = BlockchainFacade.get_instance()
    expected_block_number = blockchain_facade.get_next_block_number()
    expected_identifier = blockchain_facade.get_next_block_identifier()

    message = BlockMessage.create_from_signed_change_request(request, blockchain_facade)
    assert message.number == expected_block_number
    assert message.identifier == expected_identifier
    assert message.type == Type.NODE_DECLARATION
    assert isinstance(message.timestamp, datetime)
    assert message.timestamp.tzinfo is None

    update = message.update
    assert update.accounts.get(request.signer) == AccountState(
        account_lock=request.make_hash(),
        node=node_declaration_signed_change_request_message.node,
    )
    assert update.schedule is None


def test_serialize_deserialize_works(node_declaration_block_message):
    serialized = node_declaration_block_message.json()
    deserialized = BlockMessage.parse_raw(serialized)
    assert deserialized.type == node_declaration_block_message.type
    assert deserialized.number == node_declaration_block_message.number
    assert deserialized.identifier == node_declaration_block_message.identifier
    assert deserialized.timestamp == node_declaration_block_message.timestamp
    assert deserialized.request.signer == node_declaration_block_message.request.signer
    assert deserialized.request.signature == node_declaration_block_message.request.signature
    assert deserialized.request.message == node_declaration_block_message.request.message
    assert deserialized.request == node_declaration_block_message.request
    assert deserialized.update == node_declaration_block_message.update
    assert deserialized == node_declaration_block_message

    serialized2 = deserialized.json()
    assert serialized == serialized2


def test_node_does_not_serialize_identifier(node_declaration_block_message, regular_node_key_pair):
    serialized = node_declaration_block_message.dict()
    assert 'identifier' not in serialized['request']['message']['node']

    serialized_json = node_declaration_block_message.json()
    serialized = json.loads(serialized_json)
    assert 'identifier' not in serialized['request']['message']['node']


def test_block_identifier_is_mandatory(
    regular_node_declaration_signed_change_request, regular_node_key_pair, regular_node
):
    NodeDeclarationBlockMessage(
        number=1,
        identifier='01' * 32,
        timestamp=datetime.utcnow(),
        request=regular_node_declaration_signed_change_request,
        update=BlockMessageUpdate(accounts={'0' * 64: AccountState(node=regular_node)}),
    )

    with pytest.raises(ValidationError) as exc_info:
        NodeDeclarationBlockMessage(
            number=1,
            identifier=None,
            timestamp=datetime.utcnow(),
            request=regular_node_declaration_signed_change_request,
            update=BlockMessageUpdate(accounts={'0' * 64: AccountState(node=regular_node)}),
        )

    assert re.search(r'identifier.*none is not an allowed value', str(exc_info.value), flags=re.DOTALL)
