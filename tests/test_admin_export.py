"""
Tests for P8s Admin Export.
"""

import pytest
from datetime import datetime, date
from uuid import UUID, uuid4


class TestSerializeValue:
    """Test value serialization."""

    def test_serialize_none(self):
        """Test None serialization."""
        from p8s.admin.export import serialize_value

        assert serialize_value(None) == ""

    def test_serialize_bool(self):
        """Test bool serialization."""
        from p8s.admin.export import serialize_value

        assert serialize_value(True) == "Yes"
        assert serialize_value(False) == "No"

    def test_serialize_datetime(self):
        """Test datetime serialization."""
        from p8s.admin.export import serialize_value

        dt = datetime(2026, 1, 16, 10, 30, 0)
        assert "2026-01-16" in serialize_value(dt)

    def test_serialize_uuid(self):
        """Test UUID serialization."""
        from p8s.admin.export import serialize_value

        uid = uuid4()
        assert serialize_value(uid) == str(uid)


class TestGetFieldValue:
    """Test field value extraction."""

    def test_simple_field(self):
        """Test simple field access."""
        from p8s.admin.export import get_field_value

        class Obj:
            name = "Test"

        obj = Obj()
        assert get_field_value(obj, "name") == "Test"

    def test_nested_field(self):
        """Test nested field access."""
        from p8s.admin.export import get_field_value

        class Category:
            name = "Electronics"

        class Product:
            category = Category()

        product = Product()
        assert get_field_value(product, "category.name") == "Electronics"


class TestExportCSV:
    """Test CSV export."""

    def test_export_csv_import(self):
        """Test function can be imported."""
        from p8s.admin.export import export_csv

        assert export_csv is not None

    def test_export_empty_list(self):
        """Test exporting empty list."""
        from p8s.admin.export import export_csv

        result = export_csv([])
        assert result == ""

    def test_export_simple_objects(self):
        """Test exporting simple objects."""
        from p8s.admin.export import export_csv

        class Product:
            def __init__(self, name, price):
                self.name = name
                self.price = price

        products = [Product("A", 10), Product("B", 20)]
        csv = export_csv(products, fields=["name", "price"])

        assert "Name" in csv  # Header
        assert "A" in csv
        assert "10" in csv


class TestExportExcel:
    """Test Excel export."""

    def test_export_excel_import(self):
        """Test function can be imported."""
        from p8s.admin.export import export_excel

        assert export_excel is not None


class TestCreateCSVResponse:
    """Test CSV response creation."""

    def test_create_csv_response(self):
        """Test creating CSV response."""
        from p8s.admin.export import create_csv_response

        class Item:
            name = "Test"

        content, headers = create_csv_response([Item()], fields=["name"])

        assert "Content-Disposition" in headers
        assert "text/csv" in headers["Content-Type"]


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports."""
        from p8s.admin.export import __all__

        assert "export_csv" in __all__
        assert "export_excel" in __all__
