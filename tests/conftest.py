import pytest


@pytest.fixture(autouse=True)
def _lexicon_mode(monkeypatch):
    """Pin the detector to word lists only, so tests behave the same whether or not the model is installed.
    Tests of the hybrid mode pass semantic="hybrid" explicitly."""
    monkeypatch.setenv("PETS_SEMANTIC", "lexicon")
