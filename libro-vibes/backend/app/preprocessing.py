"""Limpieza y preparación del dataset de Goodreads."""
import ast
import re

import pandas as pd
from unidecode import unidecode

REQUIRED_COLUMNS = ["Book", "Author", "Description", "Genres", "Avg_Rating"]
OPTIONAL_COLUMNS = ["Num_Ratings", "URL"]


def normalize_title(text: str) -> str:
    """Normaliza un título para comparar: minúsculas, sin tildes ni signos."""
    text = unidecode(str(text)).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_genres(value) -> list[str]:
    """Acepta géneros como "['Fiction', 'Classics']" o "Fiction, Classics"."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        items = value
    else:
        text = str(value).strip()
        try:
            parsed = ast.literal_eval(text)
            items = parsed if isinstance(parsed, (list, tuple)) else [text]
        except (ValueError, SyntaxError):
            items = re.split(r",\s*", text.strip("[]"))
    genres = [str(g).strip(" '\"").capitalize() for g in items]
    return [g for g in genres if g]


def load_raw_data(path) -> pd.DataFrame:
    """Lee el dataset en .xlsx o .csv."""
    path = str(path)
    if path.endswith((".xlsx", ".xls")):
        return pd.read_excel(path, engine="openpyxl")
    if path.endswith(".csv"):
        return pd.read_csv(path)
    raise ValueError(f"Formato no soportado: {path}. Usa .xlsx o .csv")


def clean_books(df: pd.DataFrame) -> pd.DataFrame:
    """Valida columnas, elimina vacíos/duplicados y construye el texto para el modelo."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en el dataset: {missing}")

    keep = REQUIRED_COLUMNS + [c for c in OPTIONAL_COLUMNS if c in df.columns]
    df = df[keep].copy()

    df = df.dropna(subset=["Book"])
    df["Book"] = df["Book"].astype(str).str.strip()
    df["Author"] = df["Author"].fillna("Autor desconocido").astype(str).str.strip()
    df["Description"] = df["Description"].fillna("").astype(str)
    df["Avg_Rating"] = pd.to_numeric(df["Avg_Rating"], errors="coerce")
    if "Num_Ratings" in df.columns:
        df["Num_Ratings"] = pd.to_numeric(
            df["Num_Ratings"].astype(str).str.replace(",", ""), errors="coerce"
        )

    df["Genres_list"] = df["Genres"].apply(parse_genres)
    df["title_norm"] = df["Book"].apply(normalize_title)

    # Mismo título y autor = mismo libro.
    df = df.drop_duplicates(subset=["title_norm", "Author"]).reset_index(drop=True)

    # Los géneros se repiten para darles más peso que a la descripción.
    genres_text = df["Genres_list"].apply(" ".join)
    df["content"] = (
        df["Book"] + " " + df["Author"] + " " + genres_text + " " + genres_text + " " + df["Description"]
    )
    return df
