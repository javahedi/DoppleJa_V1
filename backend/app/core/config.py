import os

from sqlalchemy.engine import URL


def get_database_url():
    return URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("POSTGRES_USER", "doppleja_v1"),
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.getenv("DB_HOST", "db"),
        port=5432,
        database=os.getenv("POSTGRES_DB", "doppleja_v1"),
    )
