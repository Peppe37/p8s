import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from p8s.cli.main import app
from p8s.core.context import setup_context
from p8s.core.settings import Settings, DatabaseSettings
import asyncio

runner = CliRunner()

@pytest.mark.asyncio
async def test_setup_context():
    """Test functionality of setup_context utility."""
    mock_settings = Settings(database=DatabaseSettings(url="sqlite:///:memory:"))
    
    with patch("p8s.core.context.get_settings", return_value=mock_settings), \
         patch("p8s.core.context.init_db") as mock_init, \
         patch("p8s.core.context.close_db") as mock_close:
        
        async with setup_context():
            pass
            
        mock_init.assert_called_once_with(mock_settings.database)
        mock_close.assert_called_once()


def test_seed_command_script_not_found():
    """Test seed command fails if script missing."""
    # We patch Path.exists to return False
    with patch("pathlib.Path.exists", return_value=False):
        result = runner.invoke(app, ["seed", "--script", "missing.py"])
        assert result.exit_code == 1
        assert "Seed script 'missing.py' not found" in result.stdout


def test_seed_command_success():
    """Test seed command runs script successfully."""
    # Mock existence to True
    with patch("pathlib.Path.exists", return_value=True), \
         patch("runpy.run_path") as mock_run:
        
        # Invoke command
        result = runner.invoke(app, ["seed", "--script", "seed.py"])
        
        assert result.exit_code == 0
        assert "Running seed script" in result.stdout
        assert "Seeding completed successfully" in result.stdout
        # Verify runpy was called with the script path
        args, _ = mock_run.call_args
        assert "seed.py" in str(args[0])
