"""Serve the built React app (frontend/dist) from FastAPI, so the whole app runs as one
container on one URL. Unknown non-API paths return index.html (single-page app)."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = Path(os.getenv("FRONTEND_DIST", ROOT / "frontend" / "dist"))


def register_frontend(app: FastAPI, dist: Path, api_prefix: str = "/api") -> bool:
    """Serve the React build if it exists. Call after all API routes are added.

    Returns False, and changes nothing, when dist/index.html is missing (local
    development with the Vite dev server, and tests).
    """
    dist = Path(dist).resolve()
    index = dist / "index.html"
    if not index.is_file():
        return False

    # Hashed JS/CSS bundles built by Vite.
    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

    prefix = api_prefix.strip("/")

    @app.get("/{full_path:path}", include_in_schema=False)
    def frontend(full_path: str):
        # Unknown API paths must stay JSON 404s, never the web page.
        if full_path == prefix or full_path.startswith(prefix + "/"):
            raise HTTPException(status_code=404, detail="Not Found")
        # Real files at the top of dist (favicon.svg and so on), never outside it.
        if full_path:
            candidate = (dist / full_path).resolve()
            if candidate.is_file() and dist in candidate.parents:
                return FileResponse(candidate)
        # Everything else is a page of the single-page app. Don't cache index.html,
        # so a new deployment is picked up straight away.
        return FileResponse(index, headers={"Cache-Control": "no-cache"})

    return True
