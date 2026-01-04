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
def secrets_edit(c: Context, deployment: str | None = None):
    """Edit encrypted secrets file with SOPS + age.
    
    Usage: inv secrets-edit dev
           inv secrets-edit prod
    
    Opens secrets/<deployment>.env in your editor (SOPS handles encryption/decryption).
    The plaintext never touches disk outside the editor.
    
    See: https://github.com/league-infrastructure/league-infrastructure/wiki/Repository-Secrets-with-SOPS---age
    """
    if not deployment:
        print("Error: deployment name required")
        print("Usage: inv secrets-edit dev")
        print("       inv secrets-edit prod")
        sys.exit(1)
    
    secrets_dir = Path(__file__).parent / "secrets"
    secrets_file = secrets_dir / f"{deployment}.env"
    
    if not secrets_file.exists():
        print(f"Error: secrets file not found: {secrets_file}")
        print(f"\nAvailable templates:")
        for f in secrets_dir.glob("*.env.example"):
            print(f"  - {f.name}")
        sys.exit(1)
    
    # Check if sops is installed
    try:
        subprocess.run(["which", "sops"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: sops not installed")
        print("Install with: brew install sops")
        print("See: https://github.com/league-infrastructure/league-infrastructure/wiki/Repository-Secrets-with-SOPS---age")
        sys.exit(1)
    
    # Open the encrypted file in the default editor (SOPS handles encryption/decryption)
    result = subprocess.run(["sops", str(secrets_file)])
    sys.exit(result.returncode)


@task
def decrypt(c: Context, deployment: str | None = None):
    """Decrypt secrets file to .env for local development.
    
    Usage: inv secrets-decrypt dev
           inv secrets-decrypt prod
    
    This will decrypt secrets/<deployment>.env and write to .env (which is gitignored).
    
    See: https://github.com/league-infrastructure/league-infrastructure/wiki/Repository-Secrets-with-SOPS---age
    """
    if not deployment:
        print("Error: deployment name required")
        print("Usage: inv secrets-decrypt dev")
        print("       inv secrets-decrypt prod")
        sys.exit(1)
    
    secrets_dir = Path(__file__).parent / "secrets"
    secrets_file = secrets_dir / f"{deployment}.env"
    env_file = Path(__file__).parent / ".env"
    
    if not secrets_file.exists():
        print(f"Error: secrets file not found: {secrets_file}")
        print(f"\nAvailable templates:")
        for f in secrets_dir.glob("*.env.example"):
            print(f"  - {f.name}")
        sys.exit(1)
    
    # Check if sops is installed
    try:
        subprocess.run(["which", "sops"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: sops not installed")
        print("Install with: brew install sops")
        print("See: https://github.com/league-infrastructure/league-infrastructure/wiki/Repository-Secrets-with-SOPS---age")
        sys.exit(1)
    
    try:
        result = subprocess.run(
            ["sops", "-d", str(secrets_file)],
            capture_output=True,
            text=True,
            check=True,
        )
        
        with open(env_file, "w") as f:
            f.write(result.stdout)
        
        print(f"✓ Decrypted: {secrets_file.name} → .env")
        print(f"  Make sure .env is in .gitignore (it should be)")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to decrypt {secrets_file.name}")
        print(f"STDERR: {e.stderr}")
        print("Make sure you have the age key at ~/.config/sops/age/keys.txt")
        sys.exit(1)


@task
def encrypt(c: Context):
    """Encrypt secrets file using DEPLOYMENT from .env.
    
    Reads DEPLOYMENT variable from .env to determine which file to encrypt.
    Example: if DEPLOYMENT=dev in .env, encrypts secrets/dev.env
    
    Usage: inv encrypt
    
    This workflow:
    1. Decrypts secrets/<deployment>.env to plaintext
    2. Copies plaintext from .env
    3. Re-encrypts to secrets/<deployment>.env
    
    For editing encrypted files directly, use: inv secrets-edit <deployment>
    
    See: https://github.com/league-infrastructure/league-infrastructure/wiki/Repository-Secrets-with-SOPS---age
    """
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print(f"Error: .env file not found at {env_file}")
        print("First, decrypt your secrets: inv secrets-decrypt <deployment>")
        sys.exit(1)
    
    # Read DEPLOYMENT from .env
    deployment = None
    try:
        with open(env_file) as f:
            for line in f:
                if line.startswith("DEPLOYMENT="):
                    deployment = line.split("=", 1)[1].strip()
                    break
    except Exception as e:
        print(f"Error reading .env: {e}")
        sys.exit(1)
    
    if not deployment:
        print("Error: DEPLOYMENT variable not found in .env")
        print("Add a line like: DEPLOYMENT=dev")
        sys.exit(1)
    
    secrets_dir = Path(__file__).parent / "secrets"
    secrets_file = secrets_dir / f"{deployment}.env"
    
    if not secrets_file.exists():
        print(f"Error: file not found: {secrets_file}")
        sys.exit(1)
    
    # Check if sops is installed
    try:
        subprocess.run(["which", "sops"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: sops not installed")
        print("Install with: brew install sops")
        print("See: https://github.com/league-infrastructure/league-infrastructure/wiki/Repository-Secrets-with-SOPS---age")
        sys.exit(1)
    
    try:
        # Read plaintext from .env
        with open(env_file, "r") as f:
            plaintext_content = f.read()
        
        # Write plaintext to secrets file temporarily
        with open(secrets_file, "w") as f:
            f.write(plaintext_content)
        
        # Encrypt in place
        subprocess.run(
            ["sops", "-e", "-i", str(secrets_file)],
            check=True,
        )
        print(f"✓ Encrypted: {secrets_file.name} (using DEPLOYMENT={deployment})")
        print(f"  Updated secrets/{deployment}.env from .env")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to encrypt {secrets_file.name}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


@task
def updatekeys(c: Context, deployment: str | None = None):
    """Re-encrypt secrets file with updated age keys.
    
    Usage: inv secrets-updatekeys dev
           inv secrets-updatekeys prod
    
    Run this when the .sops.yaml has been updated with new developer keys.
    
    See: https://github.com/league-infrastructure/league-infrastructure/wiki/Repository-Secrets-with-SOPS---age#5-revoking-access
    """
    if not deployment:
        print("Error: deployment name required")
        print("Usage: inv secrets-updatekeys dev")
        print("       inv secrets-updatekeys prod")
        sys.exit(1)
    
    secrets_dir = Path(__file__).parent / "secrets"
    secrets_file = secrets_dir / f"{deployment}.env"
    
    if not secrets_file.exists():
        print(f"Error: file not found: {secrets_file}")
        sys.exit(1)
    
    # Check if sops is installed
    try:
        subprocess.run(["which", "sops"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: sops not installed")
        print("Install with: brew install sops")
        sys.exit(1)
    
    try:
        subprocess.run(
            ["sops", "updatekeys", str(secrets_file)],
            check=True,
        )
        print(f"✓ Re-encrypted: {secrets_file.name}")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to update keys for {secrets_file.name}")
        sys.exit(1)
