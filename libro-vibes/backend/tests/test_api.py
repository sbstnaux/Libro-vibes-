def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json["status"] == "ok"


def test_recommend_ok(client):
    res = client.post("/api/recommend", json={"libro": "The Hobbit", "n": 3})
    assert res.status_code == 200
    assert res.json["source"]["book"] == "The Hobbit"
    assert 0 < len(res.json["results"]) <= 3


def test_recommend_sin_titulo(client):
    assert client.post("/api/recommend", json={}).status_code == 400


def test_recommend_n_invalido(client):
    assert client.post("/api/recommend", json={"libro": "Dune", "n": "muchos"}).status_code == 400


def test_recommend_no_encontrado(client):
    res = client.post("/api/recommend", json={"libro": "Libro que no existe xyz"})
    assert res.status_code == 404
    assert "suggestions" in res.json


def test_search(client):
    res = client.get("/api/books/search?q=harry")
    assert res.status_code == 200
    assert len(res.json["results"]) == 2
