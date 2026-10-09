"""Modelo de recomendación basado en contenido (TF-IDF + similitud coseno)."""
from __future__ import annotations

import difflib
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from .preprocessing import clean_books, load_raw_data, normalize_title

logger = logging.getLogger(__name__)

MODEL_VERSION = 1
PUBLIC_COLUMNS = ["Book", "Author", "Avg_Rating", "Num_Ratings", "URL", "Genres_list"]


class BookNotFoundError(LookupError):
    """El título pedido no existe en el catálogo."""

    def __init__(self, query: str, suggestions: list[str]):
        super().__init__(f"Libro no encontrado: {query}")
        self.query = query
        self.suggestions = suggestions


class BookRecommender:
    def __init__(self, books: pd.DataFrame, vectorizer: TfidfVectorizer, matrix):
        self.books = books.reset_index(drop=True)
        self.vectorizer = vectorizer
        self.matrix = matrix  # sparse (n_libros x n_features), filas normalizadas L2

    # ---------- Construcción y persistencia ----------

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, max_features: int = 10000) -> BookRecommender:
        books = clean_books(df)
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=max_features,
            ngram_range=(1, 2),
            min_df=2 if len(books) > 50 else 1,
            sublinear_tf=True,
        )
        matrix = vectorizer.fit_transform(books["content"])
        books = books.drop(columns=["content", "Description", "Genres"])
        logger.info("Modelo entrenado: %d libros, %d términos", *matrix.shape)
        return cls(books, vectorizer, matrix)

    @classmethod
    def from_file(cls, data_path: str | Path, **kwargs) -> BookRecommender:
        logger.info("Leyendo dataset desde %s", data_path)
        return cls.from_dataframe(load_raw_data(data_path), **kwargs)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"version": MODEL_VERSION, "books": self.books,
             "vectorizer": self.vectorizer, "matrix": self.matrix},
            path,
            compress=3,
        )
        logger.info("Modelo guardado en %s", path)

    @classmethod
    def load(cls, path: str | Path) -> BookRecommender:
        payload = joblib.load(path)
        if payload.get("version") != MODEL_VERSION:
            raise ValueError("El modelo guardado es de otra versión; vuelve a entrenarlo.")
        return cls(payload["books"], payload["vectorizer"], payload["matrix"])

    @classmethod
    def load_or_build(cls, model_path: str | Path, data_path: str | Path) -> BookRecommender:
        """Carga el modelo pre-entrenado; si no existe, lo entrena y lo guarda."""
        model_path = Path(model_path)
        if model_path.exists():
            try:
                logger.info("Cargando modelo desde %s", model_path)
                return cls.load(model_path)
            except Exception as exc:  # modelo corrupto o de otra versión
                logger.warning("No se pudo cargar el modelo (%s). Reentrenando.", exc)

        if not Path(data_path).exists():
            raise FileNotFoundError(
                f"No se encontró el dataset en {data_path}. "
                "Colócalo en data/raw/ o ajusta DATA_PATH en el archivo .env"
            )
        recommender = cls.from_file(data_path)
        try:
            recommender.save(model_path)
        except OSError as exc:  # p. ej. sistema de archivos de solo lectura (Vercel)
            logger.warning("No se pudo guardar el modelo en %s (%s). Se usa en memoria.", model_path, exc)
        return recommender

    # ---------- Consultas ----------

    def __len__(self) -> int:
        return len(self.books)

    def _popularity(self, idx: pd.Index) -> pd.Series:
        if "Num_Ratings" in self.books.columns:
            return self.books.loc[idx, "Num_Ratings"].fillna(0)
        return pd.Series(0, index=idx)

    def find_index(self, title: str) -> int:
        """Busca un libro por título: exacto, luego prefijo, luego contenido."""
        query = normalize_title(title)
        if not query:
            raise BookNotFoundError(title, [])

        titles = self.books["title_norm"]
        for mask in (titles == query, titles.str.startswith(query), titles.str.contains(query, regex=False)):
            if mask.any():
                # Si hay varias coincidencias, la edición más popular.
                return int(self._popularity(titles[mask].index).idxmax())

        raise BookNotFoundError(title, self.suggest(title))

    def suggest(self, title: str, n: int = 5) -> list[str]:
        """Títulos parecidos para cuando el usuario escribe mal el nombre."""
        query = normalize_title(title)
        unique_titles = self.books.drop_duplicates("title_norm")
        close = difflib.get_close_matches(query, unique_titles["title_norm"].tolist(), n=n, cutoff=0.6)
        lookup = dict(zip(unique_titles["title_norm"], unique_titles["Book"], strict=True))
        return [lookup[t] for t in close]

    def search(self, query: str, limit: int = 8) -> list[dict]:
        """Autocompletado: títulos que contienen el texto, ordenados por popularidad."""
        query = normalize_title(query)
        if len(query) < 2:
            return []
        matches = self.books[self.books["title_norm"].str.contains(query, regex=False)]
        matches = matches.assign(_pop=self._popularity(matches.index)).sort_values("_pop", ascending=False)
        matches = matches.drop_duplicates("title_norm").head(limit)
        return [{"book": r.Book, "author": r.Author} for r in matches.itertuples()]

    def recommend(self, title: str, n: int = 5) -> tuple[dict, list[dict]]:
        """Devuelve (libro_encontrado, recomendaciones)."""
        idx = self.find_index(title)

        # TF-IDF ya viene normalizado, así que linear_kernel == similitud coseno.
        # Se calcula solo la fila necesaria, no la matriz n x n completa.
        scores = linear_kernel(self.matrix[idx], self.matrix).ravel()

        same_title = self.books["title_norm"].to_numpy() == self.books.at[idx, "title_norm"]
        scores[same_title] = -1  # excluye el propio libro y otras ediciones

        top = np.argsort(scores)[::-1][:n]
        top = [i for i in top if scores[i] > 0]

        results = [self._to_dict(i, score=float(scores[i])) for i in top]
        return self._to_dict(idx), results

    def _to_dict(self, i: int, score: float | None = None) -> dict:
        row = self.books.iloc[i]
        item = {
            "book": row["Book"],
            "author": row["Author"],
            "rating": None if pd.isna(row["Avg_Rating"]) else round(float(row["Avg_Rating"]), 2),
            "genres": list(row["Genres_list"])[:5],
        }
        if "Num_Ratings" in row and not pd.isna(row["Num_Ratings"]):
            item["num_ratings"] = int(row["Num_Ratings"])
        if "URL" in row and isinstance(row["URL"], str):
            item["url"] = row["URL"]
        if score is not None:
            item["similarity"] = round(score, 4)
        return item
