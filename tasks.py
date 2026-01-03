"""Development tasks for STEM League Data."""

import os
import subprocess
import sys
from pathlib import Path

from invoke import Context, task

# Path to the virtual environment
VENV_PATH = Path(__file__).parent / ".venv"


def run(c: Context, cmd: str, **kwargs):
    """Run a command with the virtual environment activated."""
    with c.prefix(f"source {VENV_PATH}/bin/activate"):
        return c.run(cmd, **kwargs)


@task
def serve(c: Context, host: str = "127.0.0.1", port: int = 8321, reload: bool = True):
    """Start the API server."""
    reload_flag = "--reload" if reload else ""
    run(c, f"uvicorn stem_league_data.app:app --host {host} --port {port} {reload_flag}")


@task
def test(c: Context, verbose: bool = False, coverage: bool = False):
    """Run tests."""
    args = []
    if verbose:
        args.append("-v")
    if coverage:
        args.append("--cov=stem_league_data")
    run(c, f"pytest {' '.join(args)}")


@task
def lint(c: Context, fix: bool = False):
    """Run linting with ruff."""
    if fix:
        run(c, "ruff check --fix .")
        run(c, "ruff format .")
    else:
        run(c, "ruff check .")
        run(c, "ruff format --check .")


@task
def typecheck(c: Context):
    """Run type checking with mypy."""
    run(c, "mypy src/stem_league_data")


@task
def fmt(c: Context):
    """Format code with ruff."""
    run(c, "ruff format .")
    run(c, "ruff check --fix .")


@task(pre=[lint, typecheck, test])
def check(c: Context):
    """Run all checks (lint, typecheck, test)."""
    print("All checks passed!")


@task
def clean(c: Context):
    """Clean build artifacts."""
    c.run("rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache")
    c.run("find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true")


@task
def build(c: Context):
    """Build the package."""
    c.run("uv build")


@task
def db_upgrade(c: Context, revision: str = "head"):
    """Run database migrations."""
    run(c, f"alembic upgrade {revision}")


@task
def db_downgrade(c: Context, revision: str = "-1"):
    """Rollback database migration."""
    run(c, f"alembic downgrade {revision}")


@task
def db_revision(c: Context, message: str = ""):
    """Create a new database migration."""
    if not message:
        print("Error: Please provide a message with -m 'description'")
        return
    run(c, f'alembic revision --autogenerate -m "{message}"')
    c.run(f'uv run alembic revision --autogenerate -m "{message}"')


@task
def encrypt(c: Context):
    """Encrypt all files in secrets/ directory."""
    secrets_dir = Path(__file__).parent / "secrets"
    if not secrets_dir.exists():
        print(f"Error: secrets directory not found at {secrets_dir}")
        sys.exit(1)
    
    # Use Python in the project venv to run encryption
    python_exe = VENV_PATH / "bin" / "python"
    script = """
from cryptography.fernet import Fernet
from pathlib import Path

secrets_dir = Path.cwd() / "secrets"
key_file = secrets_dir / ".key"

if key_file.exists():
    with open(key_file, "rb") as f:
        key = f.read()
else:
    key = Fernet.generate_key()
    with open(key_file, "wb") as f:
        f.write(key)
    print(f"Generated new encryption key: {key_file}")
    print("⚠️  SAVE THIS KEY SAFELY - you'll need it to decrypt!")

cipher = Fernet(key)

encrypted_count = 0
for env_file in sorted(secrets_dir.glob("*.env")):
    if env_file.name == ".env":
        continue
    
    with open(env_file, "rb") as f:
        plaintext = f.read()
    
    ciphertext = cipher.encrypt(plaintext)
    encrypted_file = env_file.with_suffix(".env.encrypted")
    
    with open(encrypted_file, "wb") as f:
        f.write(ciphertext)
    
    print(f"✓ Encrypted: {env_file.name} → {encrypted_file.name}")
    encrypted_count += 1

if encrypted_count == 0:
    print("No .env files found to encrypt in secrets/")
else:
    print(f"\\n✓ Encrypted {encrypted_count} file(s)")
    print(f"Key stored in: {key_file}")
"""
    
    cmd = [str(python_exe), "-c", script]
    env = os.environ.copy()
    result = subprocess.run(cmd, cwd=Path(__file__).parent, env=env)
    sys.exit(result.returncode)


@task
def decrypt(c: Context, name: str):
    """Decrypt a secrets file to .env.
    
    Usage: inv decrypt dev
    This will decrypt secrets/dev.env.encrypted to .env
    """
    secrets_dir = Path(__file__).parent / "secrets"
    key_file = secrets_dir / ".key"
    
    if not key_file.exists():
        print(f"Error: encryption key not found at {key_file}")
        sys.exit(1)
    
    # Use Python in the project venv to run decryption
    python_exe = VENV_PATH / "bin" / "python"
    script = f"""
from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path

secrets_dir = Path.cwd() / "secrets"
key_file = secrets_dir / ".key"

with open(key_file, "rb") as f:
    key = f.read()

cipher = Fernet(key)

encrypted_file = secrets_dir / "{name}.env.encrypted"
if not encrypted_file.exists():
    print(f"Error: encrypted file not found: {{encrypted_file}}")
    print(f"Available files in {{secrets_dir}}:")
    for f in secrets_dir.glob("*.env.encrypted"):
        print(f"  - {{f.name}}")
    exit(1)

try:
    with open(encrypted_file, "rb") as f:
        ciphertext = f.read()
    
    plaintext = cipher.decrypt(ciphertext)
    
    env_file = Path.cwd() / ".env"
    with open(env_file, "wb") as f:
        f.write(plaintext)
    
    print(f"✓ Decrypted: {{encrypted_file.name}} → .env")
except InvalidToken:
    print(f"Error: failed to decrypt {{encrypted_file.name}}")
    print("The encryption key may be incorrect or the file is corrupted")
    exit(1)
"""
    
    cmd = [str(python_exe), "-c", script]
    env = os.environ.copy()
    result = subprocess.run(cmd, cwd=Path(__file__).parent, env=env)
    sys.exit(result.returncode)
