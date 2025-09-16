import importlib.util

import pytest

if importlib.util.find_spec("flask") is None:
    pytest.skip("Flask não disponível", allow_module_level=True)

from artefato_tracker import app


def test_config():
    assert app.testing is False
