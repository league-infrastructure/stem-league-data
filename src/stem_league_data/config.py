"""Configuration management for STEM League Data.

Handles ROOT_DIR, BACKUP_DIR, and DATABASE_URL with support for:
- ROOT_DIR as '.' (relative to .env file) or absolute path
- BACKUP_DIR as relative to ROOT_DIR (if not absolute)
- DATABASE_URL paths as relative to ROOT_DIR (if not absolute, SQLite only)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env files before any other configuration
# This ensures environment variables are available throughout the application
# First, look for .env in current directory or parent directories
def _load_env_files():
    """Load .env files in priority order.
    
    1. Searches for .env in current directory and parent directories (up to root)
    2. Loads environment-specific file if DEPLOYMENT is set (e.g., secrets/dev.env)
    """
    # Find and load the main .env file
    current_path = Path.cwd()
    env_file = None
    
    # Search up to 10 levels of parent directories for .env
    for _ in range(10):
        if (current_path / ".env").exists():
            env_file = current_path / ".env"
            break
        if current_path.parent == current_path:
            # Reached filesystem root
            break
        current_path = current_path.parent
    
    if env_file:
        load_dotenv(env_file, override=False)
    
    # Load deployment-specific encrypted file if DEPLOYMENT is set
    deployment = os.getenv("DEPLOYMENT")
    if deployment:
        secrets_file = Path(__file__).parent.parent.parent / "secrets" / f"{deployment}.env"
        if secrets_file.exists():
            load_dotenv(secrets_file, override=False)

_load_env_files()

from typing import Optional


def get_root_dir() -> Path:
    """Get ROOT_DIR from environment.
    
    Returns:
        Path: Absolute path to root directory
              If ROOT_DIR='.' then returns directory containing .env
              If ROOT_DIR is absolute, returns that path
              Otherwise returns workspace root
    """
    root_dir_env = os.getenv("ROOT_DIR", ".")
    
    if root_dir_env == ".":
        # Find .env file in parent directories
        current = Path.cwd()
        while current != current.parent:
            if (current / ".env").exists():
                return current
            current = current.parent
        # Fallback to current working directory
        return Path.cwd()
    
    root_dir = Path(root_dir_env)
    if root_dir.is_absolute():
        return root_dir
    
    # If relative and not '.', make it relative to workspace root
    return Path.cwd() / root_dir


def resolve_path(path_str: Optional[str], base_dir: Optional[Path] = None) -> Optional[Path]:
    """Resolve a path relative to ROOT_DIR if not absolute.
    
    Args:
        path_str: Path string from config
        base_dir: Base directory (ROOT_DIR). If None, gets from get_root_dir()
    
    Returns:
        Path: Absolute path, or None if path_str is None
    """
    if not path_str:
        return None
    
    path = Path(path_str)
    
    if path.is_absolute():
        return path
    
    if base_dir is None:
        base_dir = get_root_dir()
    
    return base_dir / path


def get_backup_dir() -> Path:
    """Get the backup directory, resolving relative to ROOT_DIR.
    
    Returns:
        Path: Absolute path to backup directory
    """
    root_dir = get_root_dir()
    backup_path_env = os.getenv("BACKUP_DIR", "backups")
    
    backup_path = resolve_path(backup_path_env, root_dir)
    if backup_path is None:
        backup_path = root_dir / "backups"
    
    # Create directory if it doesn't exist
    backup_path.mkdir(parents=True, exist_ok=True)
    return backup_path


def get_database_url() -> str:
    """Get DATABASE_URL from environment, resolving SQLite paths relative to ROOT_DIR.
    
    Returns:
        str: Database URL (PostgreSQL or SQLite)
    """
    root_dir = get_root_dir()
    database_url = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{root_dir / 'stem_league_data.db'}"
    )
    
    # Only process SQLite URLs
    if not database_url.startswith("sqlite://"):
        return database_url
    
    # Parse SQLite path
    # Format: sqlite:///path/to/db.db or sqlite:////absolute/path
    if database_url.startswith("sqlite:////"):
        # Absolute path (4 slashes)
        return database_url
    
    # Relative path (3 slashes)
    # Extract the path part
    path_part = database_url[len("sqlite:///"):]
    
    # If it starts with /, it's absolute
    if path_part.startswith("/"):
        return database_url
    
    # Resolve relative to ROOT_DIR
    resolved = resolve_path(path_part, root_dir)
    if resolved:
        return f"sqlite:///{resolved}"
    
    return database_url


def get_sqlite_database_path() -> Path | None:
    """Get the SQLite database file path if using SQLite, None for PostgreSQL.
    
    Returns the resolved absolute path for SQLite databases.
    For PostgreSQL databases, returns None.
    
    Returns:
        Path: Absolute path to SQLite database file
        None: If using PostgreSQL database
    """
    database_url = get_database_url()
    
    # Not SQLite
    if not database_url.startswith("sqlite://"):
        return None
    
    # Extract path from sqlite:///path format
    if database_url.startswith("sqlite:////"):
        # Absolute path (4 slashes)
        path_str = database_url[len("sqlite:///"):]
    else:
        # Should already be resolved by get_database_url(), but extract it
        path_str = database_url[len("sqlite:///"):]
    
    return Path(path_str)


def get_dump_dir(dump_dir_override: str | None = None) -> Path:
    """Get the data dump directory path.
    
    Returns the resolved absolute path for the dump directory.
    If a specific dump_dir is provided, it's resolved relative to ROOT_DIR.
    Otherwise, defaults to <ROOT_DIR>/tests/dump.
    
    Args:
        dump_dir_override: Optional override directory path. If provided and
                          relative, will be resolved relative to ROOT_DIR.
    
    Returns:
        Path: Absolute path to dump directory
    """
    if dump_dir_override:
        return resolve_path(dump_dir_override, get_root_dir()) or Path(dump_dir_override)
    
    # Default to tests/dump relative to ROOT_DIR
    root_dir = get_root_dir()
    return root_dir / "tests" / "dump"
