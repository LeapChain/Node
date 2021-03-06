import os

import pytest
from django.conf import settings

UNITTEST_ENV_VAR_NAME = 'TNB_FOR_UNITTESTS_DISREGARD_OTHERWISE'


def test_settings_smoke():
    assert hasattr(settings, 'NODE_SIGNING_KEY')


@pytest.mark.skipif(UNITTEST_ENV_VAR_NAME not in os.environ, reason=f'{UNITTEST_ENV_VAR_NAME} env var is not set')
def test_env_var_override():
    assert getattr(settings, UNITTEST_ENV_VAR_NAME.removeprefix('TNB_'), None) == {'test': 1}  # noqa: B009
