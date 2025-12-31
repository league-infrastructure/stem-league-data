"""Smoke tests for basic functionality."""

import pytest


def test_package_imports():
    """Test that the main package can be imported."""
    import stem_league_data

    assert stem_league_data is not None


def test_models_import():
    """Test that models can be imported without circular import errors."""
    from stem_league_data.models import Base, Metro, Event, Person

    assert Base is not None
    assert Metro is not None
    assert Event is not None
    assert Person is not None
