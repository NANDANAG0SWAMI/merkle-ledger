from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class MessageRecord(Base):
    __tablename__ = "messages"
    id               = Column(Integer, primary_key=True)
    sequence_number  = Column(Integer, unique=True, index=True, nullable=False)
    payload_hash     = Column(String, nullable=False)
    epoch_id         = Column(Integer, nullable=True)
    merkle_proof     = Column(String, nullable=True)

class Epoch(Base):
    __tablename__ = "epochs"
    id                     = Column(Integer, primary_key=True, autoincrement=True)
    merkle_root            = Column(String, nullable=False)
    anchor_sequence_number = Column(Integer, nullable=True)
    anchor_timestamp       = Column(String, nullable=True)
    first_seq              = Column(Integer, nullable=False)
    last_seq               = Column(Integer, nullable=False)
    closed                 = Column(Boolean, default=False)