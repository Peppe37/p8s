"""
Tests for P8s multi-database support.
"""

import pytest


class TestDatabaseRouter:
    """Test DatabaseRouter base class."""

    def test_database_router_import(self):
        """Test DatabaseRouter can be imported."""
        from p8s.db.routers import DatabaseRouter

        assert DatabaseRouter is not None


class TestReadReplicaRouter:
    """Test ReadReplicaRouter."""

    def test_read_replica_router_import(self):
        """Test ReadReplicaRouter can be imported."""
        from p8s.db.routers import ReadReplicaRouter

        assert ReadReplicaRouter is not None

    def test_read_replica_router_defaults(self):
        """Test default aliases."""
        from p8s.db.routers import ReadReplicaRouter

        router = ReadReplicaRouter()

        assert router.primary_alias == "default"
        assert router.replica_alias == "replica"

    def test_read_replica_router_custom_aliases(self):
        """Test custom aliases."""
        from p8s.db.routers import ReadReplicaRouter

        router = ReadReplicaRouter(
            primary_alias="primary",
            replica_alias="read_replica",
        )

        assert router.primary_alias == "primary"
        assert router.replica_alias == "read_replica"

    def test_db_for_read_returns_replica(self):
        """Test read queries go to replica."""
        from p8s.db.routers import ReadReplicaRouter

        router = ReadReplicaRouter()

        # Mock model
        class MockModel:
            pass

        db = router.db_for_read(MockModel)
        assert db == "replica"

    def test_db_for_write_returns_primary(self):
        """Test write queries go to primary."""
        from p8s.db.routers import ReadReplicaRouter

        router = ReadReplicaRouter()

        class MockModel:
            pass

        db = router.db_for_write(MockModel)
        assert db == "default"

    def test_allow_migrate_primary(self):
        """Test migrations allowed on primary."""
        from p8s.db.routers import ReadReplicaRouter

        router = ReadReplicaRouter()

        class MockModel:
            pass

        assert router.allow_migrate("default", MockModel) is True

    def test_allow_migrate_replica(self):
        """Test migrations denied on replica."""
        from p8s.db.routers import ReadReplicaRouter

        router = ReadReplicaRouter()

        class MockModel:
            pass

        assert router.allow_migrate("replica", MockModel) is False


class TestModelRouter:
    """Test ModelRouter."""

    def test_model_router_import(self):
        """Test ModelRouter can be imported."""
        from p8s.db.routers import ModelRouter

        assert ModelRouter is not None

    def test_model_router_with_database(self):
        """Test routing to model-specified database."""
        from p8s.db.routers import ModelRouter

        router = ModelRouter()

        class UserModel:
            class Admin:
                database = "users_db"

        db = router.db_for_read(UserModel)
        assert db == "users_db"

    def test_model_router_no_database(self):
        """Test fallback when model has no database specified."""
        from p8s.db.routers import ModelRouter

        router = ModelRouter()

        class SimpleModel:
            pass

        db = router.db_for_read(SimpleModel)
        assert db is None


class TestRouterChain:
    """Test RouterChain."""

    def test_router_chain_import(self):
        """Test RouterChain can be imported."""
        from p8s.db.routers import RouterChain

        assert RouterChain is not None

    def test_router_chain_first_wins(self):
        """Test first router response wins."""
        from p8s.db.routers import RouterChain, ModelRouter, ReadReplicaRouter

        class UserModel:
            class Admin:
                database = "special_db"

        chain = RouterChain([
            ModelRouter(),
            ReadReplicaRouter(),
        ])

        # ModelRouter should return "special_db"
        db = chain.db_for_read(UserModel)
        assert db == "special_db"

    def test_router_chain_fallback(self):
        """Test fallback when first router returns None."""
        from p8s.db.routers import RouterChain, ModelRouter, ReadReplicaRouter

        class SimpleModel:
            pass

        chain = RouterChain([
            ModelRouter(),  # Returns None
            ReadReplicaRouter(),  # Returns "replica"
        ])

        db = chain.db_for_read(SimpleModel)
        assert db == "replica"


class TestMultiDatabase:
    """Test MultiDatabase manager."""

    def test_multi_database_import(self):
        """Test MultiDatabase can be imported."""
        from p8s.db.multi import MultiDatabase

        assert MultiDatabase is not None

    def test_multi_database_init(self):
        """Test MultiDatabase initialization."""
        from p8s.db.multi import MultiDatabase

        db = MultiDatabase({
            "default": "sqlite+aiosqlite:///:memory:",
            "replica": "sqlite+aiosqlite:///:memory:",
        })

        assert "default" in db.databases
        assert "replica" in db.databases

    def test_get_engine_creates_engine(self):
        """Test engine creation."""
        from p8s.db.multi import MultiDatabase

        # SQLite is handled automatically now
        db = MultiDatabase({
            "default": "sqlite+aiosqlite:///:memory:",
        })

        engine = db.get_engine("default")
        assert engine is not None

    def test_get_engine_unknown_alias(self):
        """Test error on unknown alias."""
        from p8s.db.multi import MultiDatabase

        db = MultiDatabase({
            "default": "sqlite+aiosqlite:///:memory:",
        })

        with pytest.raises(KeyError, match="not configured"):
            db.get_engine("unknown")

    def test_configure_databases_function(self):
        """Test configure_databases helper."""
        from p8s.db.multi import configure_databases

        db = configure_databases({
            "default": "sqlite+aiosqlite:///:memory:",
        })

        assert db is not None


class TestExports:
    """Test module exports."""

    def test_routers_all(self):
        """Test routers __all__ exports."""
        from p8s.db.routers import __all__

        assert "DatabaseRouter" in __all__
        assert "ReadReplicaRouter" in __all__
        assert "ModelRouter" in __all__
        assert "RouterChain" in __all__

    def test_multi_all(self):
        """Test multi __all__ exports."""
        from p8s.db.multi import __all__

        assert "MultiDatabase" in __all__
        assert "configure_databases" in __all__
