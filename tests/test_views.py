"""
Tests for P8s Class-Based Views.
"""

import pytest


class TestViewBase:
    """Test base View class."""

    def test_view_import(self):
        """Test View can be imported."""
        from p8s.views import View

        assert View is not None


class TestListView:
    """Test ListView class."""

    def test_listview_import(self):
        """Test ListView can be imported."""
        from p8s.views import ListView

        assert ListView is not None

    def test_listview_defaults(self):
        """Test ListView default attributes."""
        from p8s.views import ListView

        class TestListView(ListView):
            pass

        view = TestListView()
        assert view.model is None
        assert view.paginate_by == 25
        assert view.ordering is None

    def test_listview_custom_pagination(self):
        """Test ListView with custom pagination."""
        from p8s.views import ListView

        class TestListView(ListView):
            paginate_by = 50
            ordering = "-created_at"

        view = TestListView()
        assert view.paginate_by == 50
        assert view.ordering == "-created_at"


class TestDetailView:
    """Test DetailView class."""

    def test_detailview_import(self):
        """Test DetailView can be imported."""
        from p8s.views import DetailView

        assert DetailView is not None

    def test_detailview_defaults(self):
        """Test DetailView default attributes."""
        from p8s.views import DetailView

        class TestDetailView(DetailView):
            pass

        view = TestDetailView()
        assert view.model is None
        assert view.pk_field == "id"


class TestCreateView:
    """Test CreateView class."""

    def test_createview_import(self):
        """Test CreateView can be imported."""
        from p8s.views import CreateView

        assert CreateView is not None

    def test_createview_with_fields(self):
        """Test CreateView with field restrictions."""
        from p8s.views import CreateView

        class TestCreateView(CreateView):
            fields = ["name", "price"]

        view = TestCreateView()
        assert view.fields == ["name", "price"]


class TestUpdateView:
    """Test UpdateView class."""

    def test_updateview_import(self):
        """Test UpdateView can be imported."""
        from p8s.views import UpdateView

        assert UpdateView is not None

    def test_updateview_with_fields(self):
        """Test UpdateView with field restrictions."""
        from p8s.views import UpdateView

        class TestUpdateView(UpdateView):
            fields = ["name", "price"]
            pk_field = "uuid"

        view = TestUpdateView()
        assert view.fields == ["name", "price"]
        assert view.pk_field == "uuid"


class TestDeleteView:
    """Test DeleteView class."""

    def test_deleteview_import(self):
        """Test DeleteView can be imported."""
        from p8s.views import DeleteView

        assert DeleteView is not None

    def test_deleteview_defaults(self):
        """Test DeleteView default attributes."""
        from p8s.views import DeleteView

        class TestDeleteView(DeleteView):
            pass

        view = TestDeleteView()
        assert view.pk_field == "id"
        assert view.soft_delete is True

    def test_deleteview_hard_delete(self):
        """Test DeleteView with hard delete."""
        from p8s.views import DeleteView

        class TestDeleteView(DeleteView):
            soft_delete = False

        view = TestDeleteView()
        assert view.soft_delete is False


class TestAsRoute:
    """Test as_route helper function."""

    def test_as_route_import(self):
        """Test as_route can be imported."""
        from p8s.views import as_route

        assert as_route is not None


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports correct symbols."""
        from p8s.views import __all__

        assert "View" in __all__
        assert "ListView" in __all__
        assert "DetailView" in __all__
        assert "CreateView" in __all__
        assert "UpdateView" in __all__
        assert "DeleteView" in __all__
        assert "as_route" in __all__
