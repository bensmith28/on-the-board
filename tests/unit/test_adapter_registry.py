import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session, select

from src.adapters.registry import AdapterNotFoundError, get_adapter_by_type, register_adapter


def test_valid_adapter_passes():
    """Registering and looking up a valid adapter should succeed."""
    session = MagicMock(spec=Session)
    mock_adapter = MagicMock()
    mock_adapter.name = "Town Board Minutes"
    mock_adapter.status = "active"
    session.exec.return_value.first.return_value = mock_adapter

    result = get_adapter_by_type(session, source_type="meeting_minutes")
    assert result.name == "Town Board Minutes"
    assert result.status == "active"


def test_unregistered_adapter_raises():
    """Looking up a non-existent adapter should raise AdapterNotFoundError."""
    session = MagicMock(spec=Session)
    session.exec.return_value.first.return_value = None

    with pytest.raises(AdapterNotFoundError) as exc_info:
        get_adapter_by_type(session, source_type="nonexistent_adapter")
    assert exc_info.value.source_type == "nonexistent_adapter"


def test_register_adapter_creates_new():
    """register_adapter should create a new entry when none exists."""
    session = MagicMock(spec=Session)
    session.exec.return_value.first.return_value = None
    session.add = MagicMock()
    session.flush = MagicMock()

    result = register_adapter(
        session,
        name="Test Adapter",
        source_type="test_type",
        locality="Victor, NY",
        config={"key": "value"},
    )

    assert result is not None
    session.add.assert_called_once()
    session.flush.assert_called_once()


def test_register_adapter_updates_existing():
    """register_adapter should update an existing entry."""
    session = MagicMock(spec=Session)
    existing = MagicMock()
    existing.name = "Old Name"
    session.exec.return_value.first.return_value = existing

    result = register_adapter(
        session,
        name="New Name",
        source_type="test_type",
        locality="New York, NY",
        config={"key": "new_value"},
    )

    assert result.name == "New Name"
    assert result.locality == "New York, NY"
