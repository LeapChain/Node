import json

import pytest

from node.blockchain.models import Block
from node.blockchain.types import Type


@pytest.mark.usefixtures('rich_blockchain')
def test_list_blocks_smoke(api_client):
    response = api_client.get('/api/blocks/')
    assert response.status_code == 200


@pytest.mark.usefixtures('rich_blockchain')
def test_list_blocks(api_client):
    response = api_client.get('/api/blocks/')
    assert response.status_code == 200
    response_json = response.json()
    results = response_json.get('results')
    assert isinstance(results, list)
    assert len(results) == 5

    for block_number in range(5):
        block = Block.objects.get(_id=block_number)
        response_block = results[block_number]
        expected_block = json.loads(block.body)
        assert response_block == expected_block


@pytest.mark.usefixtures('bloated_blockchain')
def test_list_blocks_range(api_client):
    response = api_client.get('/api/blocks/?block_number_min=3&block_number_max=6')
    assert response.status_code == 200
    response_json = response.json()
    results = response_json.get('results')
    assert isinstance(results, list)
    assert len(results) == 4

    for index, block_number in enumerate(range(3, 7)):
        block = Block.objects.get(_id=block_number)
        response_block = results[index]
        expected_block = json.loads(block.body)
        assert response_block == expected_block


@pytest.mark.usefixtures('rich_blockchain')
def test_blocks_pagination(api_client):
    response = api_client.get('/api/blocks/?limit=1')
    assert response.status_code == 200
    response_json = response.json()
    results = response_json.get('results')
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0] == json.loads(Block.objects.get(_id=0).body)

    response = api_client.get('/api/blocks/?limit=1&offset=1')
    assert response.status_code == 200
    response_json = response.json()
    results = response_json.get('results')
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0] == json.loads(Block.objects.get(_id=1).body)

    response = api_client.get('/api/blocks/?limit=1&offset=7')
    assert response.status_code == 200
    response_json = response.json()
    results = response_json.get('results')
    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.usefixtures('rich_blockchain')
def test_list_blocks_blockchain_has_all_types():
    assert {block.get_block().message.type for block in Block.objects.order_by('_id')} == set(Type)


@pytest.mark.usefixtures('rich_blockchain')
def test_retrieve_block(api_client):
    response = api_client.get('/api/blocks/0/')
    assert response.status_code == 200
    assert response.json() == json.loads(Block.objects.get(_id=0).body)

    response = api_client.get('/api/blocks/1/')
    assert response.status_code == 200
    assert response.json() == json.loads(Block.objects.get(_id=1).body)
