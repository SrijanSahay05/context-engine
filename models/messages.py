from datetime import datetime
from sqlalchemy import (
    Integer,
    DateTime,
    func,
    CheckConstraint,
    Index,
    ForeignKey,
    Text,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base_class import Base


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.id",
    )


class Message(Base):
    __tablename__ = "message"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system', 'tool')", name="valid_message_role"
        ),
        CheckConstraint("tokens>=0", name="nonnegative_tokens"),
        Index("message_conversation_id_id_idx", "conversation_id", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    tokens: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
