from app.ingestion.embedder import generate_embedding

from app.memory.retrieval import (
    retrieve_similar_messages
)

query = "i feel exhausted"

vector = generate_embedding(query)

results = retrieve_similar_messages(
    vector 
)

print(results)