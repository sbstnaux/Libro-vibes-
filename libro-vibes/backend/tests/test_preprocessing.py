from app.preprocessing import clean_books, normalize_title, parse_genres


def test_normalize_title_quita_tildes_y_signos():
    assert normalize_title("  Cien Años de Soledad! ") == "cien anos de soledad"


def test_parse_genres_formato_lista():
    assert parse_genres("['fantasy', 'Young adult']") == ["Fantasy", "Young adult"]


def test_parse_genres_formato_coma():
    assert parse_genres("Science Fiction, Classics") == ["Science fiction", "Classics"]


def test_parse_genres_vacio():
    assert parse_genres(None) == []
    assert parse_genres(float("nan")) == []


def test_clean_books_elimina_duplicados(sample_df):
    import pandas as pd

    df = pd.concat([sample_df, sample_df.iloc[[0]]])
    assert len(clean_books(df)) == len(sample_df)
