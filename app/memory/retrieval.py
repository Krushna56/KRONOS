from sqlalchemy import text
from app.core.database import engine

def retrieve_similar_messages(vector):

    query = text("""
        SELECT message
        FROM message
        ORDER BY embedding <-> CAST(:embedding AS vector)
        LIMIT 5
        """)

    with engine.connect() as conn:

        results = conn.execute(
            query,
            {
                "embedding": vector
            }
        )

        return results.fetchall()

        