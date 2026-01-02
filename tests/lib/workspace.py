"""Workspace path utilities for tests.

Provides functions to locate the workspace root and standard test directories.
"""

from pathlib import Path


def find_workspace_root(start_path: Path | str | None = None) -> Path:
    """Find the workspace root by walking up from start_path until pyproject.toml is found.
    
    Args:
        start_path: Starting path for the search. If None, uses __file__ location.
        
    Returns:
        Path to the workspace root directory.
        
    Raises:
        FileNotFoundError: If pyproject.toml is not found in any parent directory.
    """
    if start_path is None:
        start_path = Path(__file__)
    else:
        start_path = Path(start_path)
    
    # If start_path is a file, start from its parent
    if start_path.is_file():
        current = start_path.parent
    else:
        current = start_path
    
    # Walk up the directory tree
    while current != current.parent:  # Stop at filesystem root
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    
    # Check root as well
    if (current / "pyproject.toml").exists():
        return current
    
    raise FileNotFoundError(
        f"Could not find pyproject.toml in any parent directory of {start_path}"
    )


def get_test_data_dir(start_path: Path | str | None = None) -> Path:
    """Get the tests/data directory.
    
    Args:
        start_path: Starting path for workspace search.
        
    Returns:
        Path to the tests/data directory.
    """
    root = find_workspace_root(start_path)
    return root / "tests" / "data"


def get_test_dump_dir(start_path: Path | str | None = None) -> Path:
    """Get the tests/dump directory.
    
    Args:
        start_path: Starting path for workspace search.
        
    Returns:
        Path to the tests/dump directory.
    """
    root = find_workspace_root(start_path)
    return root / "tests" / "dump"


def get_test_bin_dir(start_path: Path | str | None = None) -> Path:
    """Get the tests/bin directory.
    
    Args:
        start_path: Starting path for workspace search.
        
    Returns:
        Path to the tests/bin directory.
    """
    root = find_workspace_root(start_path)
    return root / "tests" / "bin"
