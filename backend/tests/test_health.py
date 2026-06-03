def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "online"


def test_livez(client):
    r = client.get("/livez")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


def test_readyz(client):
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["database"] == "connected"


def test_health_alias(client):
    r = client.get("/health")
    assert r.status_code == 200
