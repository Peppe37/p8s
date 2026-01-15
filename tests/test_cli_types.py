import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from p8s.cli.main import app
import sys
from pathlib import Path

runner = CliRunner()

def test_types_command_success(tmp_path):
    """Test successful types generation."""
    mock_app = MagicMock()
    mock_app.openapi.return_value = {"openapi": "3.0.0", "info": {"title": "Test"}}
    
    with patch.dict(sys.modules, {"backend.main": MagicMock(app=mock_app)}):
        with patch("subprocess.run") as mock_run:
            with patch("pathlib.Path.cwd", return_value=tmp_path):
                result = runner.invoke(app, ["types", "--output", "src/types.ts"])
                
                assert result.exit_code == 0
                assert "Types generated" in result.stdout
                mock_app.openapi.assert_called_once()
                mock_run.assert_called_once()

def test_types_command_import_error():
    """Test failure when backend can't be imported."""
    # We patch sys.path to ensure backend module cannot be found
    # And we remove backend from sys.modules if present
    with patch.dict(sys.modules):
        sys.modules.pop("backend", None)
        sys.modules.pop("backend.main", None)
        
        with patch("sys.path", []):
            # Also patch subprocess just in case validation fails and it proceeds
            with patch("subprocess.run") as mock_run:
                result = runner.invoke(app, ["types"])
                
                assert result.exit_code == 1
                assert "Could not load" in result.stdout
                mock_run.assert_not_called()
