import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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