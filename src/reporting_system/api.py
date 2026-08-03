"""Backward-compatibility module re-exporting FastAPI app from main.py."""

from main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8001, reload=True)
