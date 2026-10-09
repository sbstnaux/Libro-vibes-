"""Libro Vibes: API de recomendación de libros."""
import logging

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from .config import Config
from .recommender import BookRecommender


def create_app(config: type[Config] = Config, recommender: BookRecommender | None = None) -> Flask:
    """Application factory: crea y configura la app de Flask."""
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = Flask(__name__, static_folder=None)
    app.config.from_object(config)

    CORS(app, resources={r"/api/*": {"origins": config.CORS_ORIGINS}})

    # El modelo se carga una sola vez al arrancar, no en cada petición.
    app.extensions["recommender"] = recommender or BookRecommender.load_or_build(
        model_path=config.MODEL_PATH,
        data_path=config.DATA_PATH,
    )

    from .routes import api

    app.register_blueprint(api, url_prefix="/api")

    # En local, Flask también sirve el frontend para no necesitar otro servidor.
    if config.SERVE_FRONTEND:
        frontend_dir = config.FRONTEND_DIR

        @app.get("/")
        def index():
            return send_from_directory(frontend_dir, "index.html")

        @app.get("/<path:filename>")
        def static_files(filename: str):
            return send_from_directory(frontend_dir, filename)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="Recurso no encontrado"), 404

    @app.errorhandler(500)
    def server_error(_error):
        return jsonify(error="Error interno del servidor"), 500

    return app
