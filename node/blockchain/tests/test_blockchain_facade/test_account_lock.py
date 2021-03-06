import pytest

from node.blockchain.facade import BlockchainFacade
from node.blockchain.inner_models import NodeDeclarationSignedChangeRequest


@pytest.mark.usefixtures('base_blockchain')
def test_account_lock_change_when_block_is_added(
    node_declaration_signed_change_request_message, regular_node_key_pair, primary_validator_key_pair
):
    blockchain_facade = BlockchainFacade.get_instance()

    assert blockchain_facade.get_account_lock(regular_node_key_pair.public) == regular_node_key_pair.public

    request = NodeDeclarationSignedChangeRequest.create_from_signed_change_request_message(
        message=node_declaration_signed_change_request_message,
        signing_key=regular_node_key_pair.private,
    )

    blockchain_facade.add_block_from_signed_change_request(request, signing_key=primary_validator_key_pair.private)

    account_lock = blockchain_facade.get_account_lock(regular_node_key_pair.public)
    assert account_lock != regular_node_key_pair.public
    assert account_lock == request.make_hash()


@pytest.mark.usefixtures('base_blockchain')
def test_get_account_balance(treasury_account_key_pair, treasury_amount):
    blockchain_facade = BlockchainFacade.get_instance()
    assert blockchain_facade.get_account_balance(treasury_account_key_pair.public) == treasury_amount


@pytest.mark.django_db
def test_get_account_balance_for_unknown_account_number():
    blockchain_facade = BlockchainFacade.get_instance()
    assert blockchain_facade.get_account_balance('0' * 64) == 0
