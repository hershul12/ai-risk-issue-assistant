"""The API under /api, and serving the built React app from FastAPI."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.frontend import register_frontend
from app.main import router

INDEX = '<!doctype html><html><body><div id="root"></div></body></html>'


# ---- every API route also works under /api ----

@pytest.mark.parametrize("path", ["/health", "/items", "/dashboard/summary", "/policies"])
def test_get_routes_work_at_root_and_under_api(client, path):
    root, prefixed = client.get(path), client.get("/api" + path)
    assert root.status_code == prefixed.status_code == 200
    assert root.json() == prefixed.json()


def test_write_routes_and_roles_work_under_api(client):
    item = {
        "title": "Vendor delay under api",
        "description": "Vendor may miss the integration milestone.",
        "item_type": "Risk", "category": "Vendor", "probability": 2, "impact": 3,
        "owner": "Alex", "due_date": "2030-01-01",
    }
    assert client.post("/api/items", json=item, headers={"X-Role": "Risk Owner"}).status_code == 403
    created = client.post("/api/items", json=item, headers={"X-Role": "Project Manager"})
    assert created.status_code == 201
    item_id = created.json()["id"]
    # Same record is visible on both paths.
    assert client.get(f"/items/{item_id}").json() == client.get(f"/api/items/{item_id}").json()
    assert client.get("/api/items/999999").status_code == 404


def test_every_route_has_an_api_copy_in_the_docs(client):
    schema = client.get("/openapi.json").json()["paths"]
    assert router.routes, "router has no routes"
    for route in router.routes:
        methods = {m.lower() for m in route.methods}
        assert methods <= set(schema[route.path]), route.path
        assert methods <= set(schema["/api" + route.path]), route.path
    # The web page catch-all is not part of the API docs.
    assert not any("full_path" in p for p in schema)


# ---- serving the React build ----

def make_app(dist):
    app = FastAPI()
    app.include_router(router)
    app.include_router(router, prefix="/api")
    served = register_frontend(app, dist)
    return app, served


@pytest.fixture
def dist(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text(INDEX, encoding="utf-8")
    (tmp_path / "assets" / "app-123.js").write_text("console.log('app')", encoding="utf-8")
    (tmp_path / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path.parent / "secret.txt").write_text("outside dist", encoding="utf-8")
    return tmp_path


def test_serves_index_assets_and_spa_fallback(dist):
    app, served = make_app(dist)
    assert served is True
    web = TestClient(app)

    home = web.get("/")
    assert home.status_code == 200 and '<div id="root">' in home.text
    assert home.headers["cache-control"] == "no-cache"
    assert web.get("/assets/app-123.js").text == "console.log('app')"
    assert web.get("/favicon.svg").text == "<svg/>"
    # Unknown page paths get the app, so the browser can handle them.
    assert '<div id="root">' in web.get("/some/page").text


def test_api_paths_are_never_the_web_page(dist):
    web = TestClient(make_app(dist)[0])
    assert web.get("/api/health").json() == {"status": "ok"}
    assert web.get("/health").json() == {"status": "ok"}
    for path in ("/api", "/api/", "/api/does-not-exist"):
        res = web.get(path)
        assert res.status_code == 404
        assert res.headers["content-type"].startswith("application/json")
    # A missing asset is not replaced by the page.
    assert web.get("/assets/missing.js").status_code == 404


def test_files_outside_dist_are_not_served(dist):
    web = TestClient(make_app(dist)[0])
    res = web.get("/..%2Fsecret.txt")
    assert "outside dist" not in res.text


def test_no_build_means_no_frontend(tmp_path):
    app, served = make_app(tmp_path / "missing")
    assert served is False
    web = TestClient(app)
    assert web.get("/").status_code == 404
    assert web.get("/api/health").json() == {"status": "ok"}
