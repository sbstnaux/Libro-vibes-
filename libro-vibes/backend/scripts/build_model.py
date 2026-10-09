"""Entrena el modelo y lo guarda en disco.

Uso (desde la carpeta backend/):
    python -m scripts.build_model
    python -m scripts.build_model --data ../data/raw/otro.csv --output ../data/processed/recommender.joblib
"""
import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Config  # noqa: E402
from app.recommender import BookRecommender  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena el recomendador de libros.")
    parser.add_argument("--data", type=Path, default=Config.DATA_PATH, help="Ruta al dataset (.xlsx o .csv)")
    parser.add_argument("--output", type=Path, default=Config.MODEL_PATH, help="Ruta de salida del modelo")
    parser.add_argument("--max-features", type=int, default=10000)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    start = time.perf_counter()
    recommender = BookRecommender.from_file(args.data, max_features=args.max_features)
    recommender.save(args.output)
    logging.info("Listo en %.1f s", time.perf_counter() - start)


if __name__ == "__main__":
    main()
