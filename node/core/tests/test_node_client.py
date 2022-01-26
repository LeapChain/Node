from types import GeneratorType
from unittest.mock import MagicMock, call

import pytest
from requests.exceptions import HTTPError

from node.blockchain.facade import BlockchainFacade
from node.blockchain.inner_models.node import Node as InnerNode
from node.blockchain.models import Block, Node
from node.blockchain.tests.base import get_node_declaration_signed_change_request
from node.core.tests.base import make_node
from node.core.utils.cryptography import generate_key_pair, get_node_identifier


def test_send_scr_to_address(
    primary_validator_node, regular_node_declaration_signed_change_request, mocked_node_client
):
    client = mocked_node_client

    address = primary_validator_node.addresses[0]
    scr = regular_node_declaration_signed_change_request

    rv = MagicMock()
    rv.status_code = 201
    client.requests_post.return_value = rv
    client.send_scr_to_address(address, scr)
    client.requests_post.assert_called_once_with(
        str(address) + 'api/signed-change-requests/',
        json=None,
        data=scr.json(),
        headers={'Content-Type': 'application/json'},
        timeout=2,
    )


@pytest.mark.django_db
@pytest.mark.usefixtures('base_blockchain')
def test_send_scr_to_address_integration(
    test_server_address, regular_node_declaration_signed_change_request, smart_mocked_node_client
):
    assert BlockchainFacade.get_next_block_number() == 1
    assert not Node.objects.filter(_id=regular_node_declaration_signed_change_request.signer).exists()

    client = smart_mocked_node_client
    scr = regular_node_declaration_signed_change_request
    response = client.send_scr_to_address(test_server_address, scr)
    assert response.status_code == 201

    assert BlockchainFacade.get_next_block_number() == 2
    assert Node.objects.filter(_id=regular_node_declaration_signed_change_request.signer).exists()


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
    client.send_scr_to_node(node, scr)
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


@pytest.mark.django_db
@pytest.mark.usefixtures('rich_blockchain')
@pytest.mark.parametrize('block_identifier, block_number', (
    (0, 0),
    (1, 1),
    (2, 2),
    ('last', 2),
))
def test_get_block_raw(test_server_address, smart_mocked_node_client, block_identifier, block_number):
    block = smart_mocked_node_client.get_block_raw(test_server_address, block_identifier)
    expected_block = Block.objects.get(_id=block_number)
    assert block == expected_block.body


@pytest.mark.django_db
def test_get_block_raw_last_from_empty_blockchain(test_server_address, smart_mocked_node_client):
    block = smart_mocked_node_client.get_block_raw(test_server_address, 'last')
    assert block is None


@pytest.mark.usefixtures('rich_blockchain')
def test_list_nodes(test_server_address, smart_mocked_node_client):
    client = smart_mocked_node_client

    node_generator = client.list_nodes(test_server_address)

    assert isinstance(node_generator, GeneratorType)
    nodes = list(node_generator)
    assert len(nodes) == 3

    node1, node2, node3 = nodes

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
    ]
    assert node2.fee == 4

    assert isinstance(node3, InnerNode)
    assert node3.identifier == 'b9dc49411424cce606d27eeaa8d74cb84826d8a1001d17603638b73bdc6077f1'
    assert node3.addresses == [
        'http://not-existing-primary-validator-address-674898923.com:8555/',
    ]
    assert node3.fee == 4


@pytest.mark.django_db
def test_list_nodes_without_nodes(test_server_address, smart_mocked_node_client):
    client = smart_mocked_node_client
    node_generator = client.list_nodes(test_server_address)
    nodes = list(node_generator)
    assert len(nodes) == 0


@pytest.mark.django_db
def test_list_nodes_pagination(test_server_address, base_blockchain, smart_mocked_node_client, primary_validator_node):
    blockchain_facade = BlockchainFacade.get_instance()

    for _ in range(24):
        node_key_pair = generate_key_pair()
        node = make_node(node_key_pair, [primary_validator_node.addresses[0], 'http://testserver/'])
        node_declaration_scr = get_node_declaration_signed_change_request(node, node_key_pair)
        Block.objects.add_block_from_signed_change_request(
            signed_change_request=node_declaration_scr,
            blockchain_facade=blockchain_facade,
            signing_key=node_key_pair.private,
            validate=False,
        )

    client = smart_mocked_node_client
    node_generator = client.list_nodes(test_server_address)
    nodes = list(node_generator)
    assert len(nodes) == 25
