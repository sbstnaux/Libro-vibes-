import pandas as pd
import pytest

from app import create_app
from app.config import Config
from app.recommender import BookRecommender

SAMPLE_BOOKS = [
    ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "A young wizard attends a school of magic and wizardry.", "['Fantasy', 'Magic', 'Young Adult']", 4.47, "9,278,135"),
    ("Harry Potter and the Chamber of Secrets", "J.K. Rowling", "The young wizard returns to the school of magic for a second year.", "['Fantasy', 'Magic', 'Young Adult']", 4.43, "3,500,000"),
    ("The Hobbit", "J.R.R. Tolkien", "A hobbit joins a quest with dwarves and a wizard to reclaim treasure from a dragon.", "['Fantasy', 'Classics', 'Adventure']", 4.28, "3,800,000"),
    ("Pride and Prejudice", "Jane Austen", "A witty romance about manners, marriage and society in England.", "['Classics', 'Romance']", 4.28, "4,000,000"),
    ("Emma", "Jane Austen", "A young woman plays matchmaker in her English village, romance and society.", "['Classics', 'Romance']", 4.02, "800,000"),
    ("Dune", "Frank Herbert", "Politics, religion and ecology on a desert planet in the far future.", "Science Fiction, Classics", 4.27, "1,400,000"),
    ("Cien años de soledad", "Gabriel García Márquez", "The Buendía family across generations in the town of Macondo, magical realism.", "['Fiction', 'Magical Realism', 'Classics']", 4.11, "900,000"),
]


@pytest.fixture(scope="session")
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(SAMPLE_BOOKS, columns=["Book", "Author", "Description", "Genres", "Avg_Rating", "Num_Ratings"])


@pytest.fixture(scope="session")
def recommender(sample_df) -> BookRecommender:
    return BookRecommender.from_dataframe(sample_df)


@pytest.fixture()
def client(recommender):
    class TestConfig(Config):
        TESTING = True
        SERVE_FRONTEND = False

    return create_app(TestConfig, recommender=recommender).test_client()
