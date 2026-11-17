# Import Base and all models for Alembic's target_metadata
from db.base_class import Base
from models.messages import Message, Conversation

__all__ = ["Base", "Message", "Conversation"]
