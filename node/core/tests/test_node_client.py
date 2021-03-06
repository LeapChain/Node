from types import GeneratorType
from unittest.mock import MagicMock, call, patch

import pytest
from requests.exceptions import HTTPError

from node.blockchain.facade import BlockchainFacade
from node.blockchain.inner_models import Block, BlockConfirmation
from node.blockchain.inner_models import Node as InnerNode
from node.blockchain.models import Block as ORMBlock
from node.blockchain.models import BlockConfirmation as ORMBlockConfirmation
from node.blockchain.models import Node as ORMNode
from node.blockchain.models import PendingBlock
from node.blockchain.tests.factories.block import make_block
from node.blockchain.tests.factories.block_message.node_declaration import make_node_declaration_block_message
from node.blockchain.tests.factories.node import make_node
from node.core.utils.cryptography import get_node_identifier


def test_send_signed_change_request(
    primary_validator_node, regular_node_declaration_signed_change_request, mocked_node_client
):
    client = mocked_node_client

    address = primary_validator_node.addresses[0]
    scr = regular_node_declaration_signed_change_request

    rv = MagicMock()
    rv.status_code = 201
    client.requests_post.return_value = rv
    client.send_signed_change_request(address, scr)
    client.requests_post.assert_called_once_with(
        str(address) + 'api/signed-change-requests/',
        json=None,
        data=scr.json(),
        headers={'Content-Type': 'application/json'},
        timeout=2,
    )


@pytest.mark.usefixtures('base_blockchain', 'as_primary_validator')
def test_send_scr_to_address_integration(
    test_server_address, regular_node_declaration_signed_change_request, smart_mocked_node_client
):
    blockchain_facade = BlockchainFacade.get_instance()
    assert blockchain_facade.get_next_block_number() == 1
    assert blockchain_facade.get_node_by_identifier(regular_node_declaration_signed_change_request.signer) is None
    assert not ORMNode.objects.filter(_id=regular_node_declaration_signed_change_request.signer).exists()

    client = smart_mocked_node_client
    scr = regular_node_declaration_signed_change_request
    response = client.send_signed_change_request(test_server_address, scr)
    assert response.status_code == 201

    assert BlockchainFacade.get_instance().get_next_block_number() == 2
    assert blockchain_facade.get_node_by_identifier(regular_node_declaration_signed_change_request.signer) is not None
    assert ORMNode.objects.filter(_id=regular_node_declaration_signed_change_request.signer).exists()


def test_send_scr_to_node(
    primary_validator_key_pair, primary_validator_node, regular_node_declaration_signed_change_request,
    mocked_node_client
):
    response1 = MagicMock()
    response1.status_code = 503
    response1.raise_for_status.side_effect = HTTPError
    response2 = MagicMock()
    response2.status_code = 201

    client = mocked_node_client
    client.requests_post.side_effect = [response1, response2]

    node = make_node(primary_validator_key_pair, [primary_validator_node.addresses[0], 'http://testserver/'])
    scr = regular_node_declaration_signed_change_request
    client.send_signed_change_request(node, scr)
    client.requests_post.assert_has_calls((
        call(
            str(primary_validator_node.addresses[0]) + 'api/signed-change-requests/',
            json=None,
            data=scr.json(),
            headers={'Content-Type': 'application/json'},
            timeout=2,
        ),
        call(
            'http://testserver/api/signed-change-requests/',
            json=None,
            data=scr.json(),
            headers={'Content-Type': 'application/json'},
            timeout=2,
        ),
    ))


@pytest.mark.usefixtures('base_blockchain', 'as_confirmation_validator')
def test_send_block_to_address_integration(
    test_server_address, primary_validator_key_pair, regular_node, regular_node_key_pair, smart_mocked_node_client
):
    assert not PendingBlock.objects.exists()

    facade = BlockchainFacade.get_instance()
    block_message = make_node_declaration_block_message(regular_node, regular_node_key_pair, facade)

    assert facade.get_primary_validator().identifier == primary_validator_key_pair.public
    block = make_block(block_message, primary_validator_key_pair.private)

    for block_arg in (block, block.json()):
        with patch('node.blockchain.serializers.block.start_process_pending_blocks_task') as mock:
            response = smart_mocked_node_client.send_block(test_server_address, block_arg)

        assert response.status_code == 204
        mock.assert_called()
        pending_block = PendingBlock.objects.get_or_none(number=block.get_block_number(), hash=block.make_hash())
        assert pending_block
        assert pending_block.body == block.json()
        PendingBlock.objects.all().delete()


@pytest.mark.usefixtures('rich_blockchain', 'as_confirmation_validator')
def test_send_confirmation_to_cv(
    next_block, test_server_address, confirmation_validator_key_pair_2, smart_mocked_node_client
):
    assert not ORMBlockConfirmation.objects.exists()

    block = next_block
    assert BlockchainFacade.get_instance().get_next_block_number() >= block.get_block_number()

    hash_ = block.make_hash()
    block_confirmation = BlockConfirmation.create(
        block.get_block_number(), hash_, confirmation_validator_key_pair_2.private
    )
    payload = block_confirmation.json()
    response = smart_mocked_node_client.send_block_confirmation(test_server_address, block_confirmation)

    assert response.status_code == 201
    confirmation_orm = ORMBlockConfirmation.objects.get_or_none(number=block_confirmation.get_number(), hash=hash_)
    assert confirmation_orm
    assert confirmation_orm.signer == confirmation_validator_key_pair_2.public
    assert confirmation_orm.body == payload


@pytest.mark.django_db
@pytest.mark.usefixtures('rich_blockchain')
@pytest.mark.parametrize('block_identifier, block_number', (
    (0, 0),
    (1, 1),
    (2, 2),
    ('last', 6),
))
def test_get_block_raw(test_server_address, smart_mocked_node_client, block_identifier, block_number):
    block = smart_mocked_node_client.get_block_raw(test_server_address, block_identifier)
    expected_block = ORMBlock.objects.get(_id=block_number)
    assert block == expected_block.body


@pytest.mark.django_db
def test_get_block_raw_last_from_empty_blockchain(test_server_address, smart_mocked_node_client):
    block = smart_mocked_node_client.get_block_raw(test_server_address, 'last')
    assert block is None


@pytest.mark.usefixtures('rich_blockchain')
def test_yield_nodes(test_server_address, smart_mocked_node_client):
    client = smart_mocked_node_client

    node_generator = client.yield_nodes(test_server_address)

    assert isinstance(node_generator, GeneratorType)
    nodes = list(node_generator)
    assert len(nodes) == 5

    node1, _, node2, node3, _ = nodes

    assert isinstance(node1, InnerNode)
    assert node1.identifier == '1c8e5f54a15b63a9f3d540ce505fd0799575ffeaac62ce625c917e6d915ea8bb'
    assert node1.addresses == [
        'http://not-existing-node-address-674898923.com:8555/',
    ]
    assert node1.fee == 4

    assert isinstance(node2, InnerNode)
    assert node2.identifier == get_node_identifier()
    assert node2.addresses == [
        'http://not-existing-self-address-674898923.com:8555/',
        test_server_address,
    ]
    assert node2.fee == 4

    assert isinstance(node3, InnerNode)
    assert node3.identifier == 'b9dc49411424cce606d27eeaa8d74cb84826d8a1001d17603638b73bdc6077f1'
    assert node3.addresses == [
        'http://not-existing-primary-validator-address-674898923.com:8555/',
    ]
    assert node3.fee == 4


@pytest.mark.django_db
def test_yield_nodes_without_nodes(test_server_address, smart_mocked_node_client):
    client = smart_mocked_node_client
    node_generator = client.yield_nodes(test_server_address)
    nodes = list(node_generator)
    assert len(nodes) == 0


@pytest.mark.django_db
def test_yield_nodes_pagination(
    test_server_address, bloated_blockchain, smart_mocked_node_client, primary_validator_node,
    primary_validator_key_pair
):
    assert len(list(smart_mocked_node_client.yield_nodes(test_server_address))) == 29


@pytest.mark.django_db
def test_yield_blocks(test_server_address, bloated_blockchain, smart_mocked_node_client):
    blocks = list(smart_mocked_node_client.yield_blocks_dict(test_server_address))
    assert len(blocks) == 31
    assert [block['message']['number'] for block in blocks] == list(range(31))
    block_objs = [Block.parse_obj(block) for block in blocks]
    assert block_objs == [block.get_block() for block in ORMBlock.objects.all().order_by('_id')]


@pytest.mark.django_db
def test_yield_blocks_filtered(test_server_address, bloated_blockchain, smart_mocked_node_client):
    blocks = list(
        smart_mocked_node_client.yield_blocks_dict(test_server_address, block_number_min=3, block_number_max=6)
    )
    assert len(blocks) == 4
    assert [block['message']['number'] for block in blocks] == list(range(3, 7))
    block_objs = [Block.parse_obj(block) for block in blocks]
    assert block_objs == [
        block.get_block() for block in ORMBlock.objects.all().filter(_id__gte=3, _id__lte=6).order_by('_id')
    ]


@pytest.mark.usefixtures('rich_blockchain')
def test_get_node_online_address(test_server_address, smart_mocked_node_client, self_node):
    assert self_node.identifier == get_node_identifier()
    assert test_server_address in self_node.addresses
    assert BlockchainFacade.get_instance().get_node_by_identifier(self_node.identifier) is not None
    assert ORMNode.objects.filter(_id=self_node.identifier).exists()

    assert smart_mocked_node_client.get_node_online_address(self_node) == test_server_address

    with patch.object(smart_mocked_node_client, 'requests_get', side_effect=HTTPError()):
        assert smart_mocked_node_client.get_node_online_address(self_node) is None
