from app.core.database import Base, engine
from app.models.message_models import Base



Base.metadata.create_all(bind=engine)

print("table created")

