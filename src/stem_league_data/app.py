"""FastAPI application for STEM League Data."""

from fastapi import FastAPI

app = FastAPI(
    title="STEM League Data",
    description="Data model and API for the League STEM network",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Welcome to STEM League Data API"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
