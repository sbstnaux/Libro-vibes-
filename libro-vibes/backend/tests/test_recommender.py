import pytest

from app.recommender import BookNotFoundError, BookRecommender


def test_recomienda_libros_parecidos(recommender):
    source, results = recommender.recommend("harry potter and the sorcerer's stone", n=2)
    assert source["book"].startswith("Harry Potter")
    assert results[0]["book"] == "Harry Potter and the Chamber of Secrets"


def test_no_se_recomienda_a_si_mismo(recommender):
    source, results = recommender.recommend("Emma", n=5)
    assert source["book"] not in [r["book"] for r in results]


def test_busqueda_sin_tildes(recommender):
    source, _ = recommender.recommend("cien anos de soledad")
    assert source["author"] == "Gabriel García Márquez"


def test_busqueda_parcial(recommender):
    source, _ = recommender.recommend("hobbit")
    assert source["book"] == "The Hobbit"


def test_libro_inexistente_da_sugerencias(recommender):
    with pytest.raises(BookNotFoundError) as exc:
        recommender.recommend("Pride and Prejudise")  # error de escritura
    assert "Pride and Prejudice" in exc.value.suggestions


def test_guardar_y_cargar(recommender, tmp_path):
    path = tmp_path / "model.joblib"
    recommender.save(path)
    loaded = BookRecommender.load(path)
    assert len(loaded) == len(recommender)
    assert loaded.recommend("Dune")[0]["book"] == "Dune"
