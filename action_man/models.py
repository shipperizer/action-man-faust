from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from action_man.db import Base


class Action(Base):
    """ """
    __tablename__ = 'action'

    id = Column(UUID(as_uuid=True), primary_key=True)
    experiment_id = Column(UUID(as_uuid=True), index=True)
    variant_id = Column(UUID(as_uuid=True), index=True)
    reward = Column(Integer)
    context = Column(JSONB)
    last_modified = Column(DateTime(), nullable=False, server_default=func.now())
