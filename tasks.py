"""Development tasks for STEM League Data."""

from pathlib import Path

from invoke import Context, task

# Path to the virtual environment
VENV_PATH = Path(__file__).parent / ".venv"


def run(c: Context, cmd: str, **kwargs):
    """Run a command with the virtual environment activated."""
    with c.prefix(f"source {VENV_PATH}/bin/activate"):
        return c.run(cmd, **kwargs)


@task
def serve(c: Context, host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
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
