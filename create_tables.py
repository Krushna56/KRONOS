from sqlalchemy import text
from app.core.database import engine

with engine.connect() as conn:
    print("Database:", conn.execute(text("SELECT current_database()")).scalar())
    print("Version:", conn.execute(text("SELECT version()")).scalar())

    extensions = conn.execute(
        text("SELECT extname FROM pg_extension")
    ).fetchall()

    print("Extensions:", extensions)