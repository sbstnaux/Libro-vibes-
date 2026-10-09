"""Endpoints de la API REST."""
from flask import Blueprint, current_app, jsonify, request

from .recommender import BookNotFoundError, BookRecommender

api = Blueprint("api", __name__)


def _recommender() -> BookRecommender:
    return current_app.extensions["recommender"]


@api.get("/health")
def health():
    return jsonify(status="ok", books=len(_recommender()))


@api.get("/books/search")
def search_books():
    query = request.args.get("q", "").strip()
    return jsonify(results=_recommender().search(query))


@api.post("/recommend")
def recommend():
    data = request.get_json(silent=True) or {}

    # Se acepta "libro" (nombre original) o "title".
    title = str(data.get("libro") or data.get("title") or "").strip()
    if not title:
        return jsonify(error="Escribe el título de un libro."), 400
    if len(title) > 200:
        return jsonify(error="El título es demasiado largo."), 400

    cfg = current_app.config
    try:
        n = int(data.get("n", cfg["DEFAULT_RESULTS"]))
    except (TypeError, ValueError):
        return jsonify(error="'n' debe ser un número entero."), 400
    n = max(1, min(n, cfg["MAX_RESULTS"]))

    try:
        source, results = _recommender().recommend(title, n=n)
    except BookNotFoundError as exc:
        return jsonify(error="Libro no encontrado", query=exc.query, suggestions=exc.suggestions), 404

    return jsonify(source=source, results=results)
