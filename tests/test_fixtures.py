"""
Tests for P8s Fixtures.
"""

import pytest
import json
from datetime import datetime
from uuid import uuid4


class TestJSONEncoder:
    """Test custom JSON encoder."""

    def test_encoder_import(self):
        """Test encoder can be imported."""
        from p8s.cli.fixtures import JSONEncoder

        assert JSONEncoder is not None

    def test_encode_datetime(self):
        """Test datetime encoding."""
        from p8s.cli.fixtures import JSONEncoder

        dt = datetime(2026, 1, 16, 10, 30)
        result = json.dumps({"dt": dt}, cls=JSONEncoder)

        assert "2026-01-16" in result

    def test_encode_uuid(self):
        """Test UUID encoding."""
        from p8s.cli.fixtures import JSONEncoder

        uid = uuid4()
        result = json.dumps({"id": uid}, cls=JSONEncoder)

        assert str(uid) in result


class TestSerializeModel:
    """Test model serialization."""

    def test_serialize_dict_obj(self):
        """Test serializing object with __dict__."""
        from p8s.cli.fixtures import serialize_model

        class Obj:
            def __init__(self):
                self.name = "Test"
                self._private = "hidden"

        result = serialize_model(Obj())

        assert "name" in result
        assert "_private" not in result


class TestParseFixture:
    """Test fixture parsing."""

    def test_parse_single_fixture(self):
        """Test parsing single fixture."""
        from p8s.cli.fixtures import parse_fixture

        content = '{"model": "Product", "items": []}'
        result = parse_fixture(content)

        assert len(result) == 1
        assert result[0]["model"] == "Product"

    def test_parse_list_fixtures(self):
        """Test parsing list of fixtures."""
        from p8s.cli.fixtures import parse_fixture

        content = '[{"model": "A"}, {"model": "B"}]'
        result = parse_fixture(content)

        assert len(result) == 2


class TestWriteFixture:
    """Test fixture writing."""

    def test_write_fixture_import(self):
        """Test function can be imported."""
        from p8s.cli.fixtures import write_fixture

        assert write_fixture is not None


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports."""
        from p8s.cli.fixtures import __all__

        assert "dump_model" in __all__
        assert "load_fixture" in __all__
        assert "parse_fixture" in __all__
