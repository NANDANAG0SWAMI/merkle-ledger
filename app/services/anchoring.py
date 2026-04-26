import hashlib
import json
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.epoch import MessageRecord, Epoch
from app.services.merkle import merkle_root, inclusion_proof
from app.services.hedera import submit_anchor
from app.config import settings

def hash_payload(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

async def record_message(db: AsyncSession, sequence_number: int, payload: dict) -> MessageRecord:
    raw = json.dumps(payload, sort_keys=True)
    record = MessageRecord(sequence_number=sequence_number, payload_hash=hash_payload(raw))
    db.add(record)
    await db.commit()
    await db.refresh(record)
    await _maybe_anchor(db)
    return record

async def _maybe_anchor(db: AsyncSession):
    result = await db.execute(
        select(MessageRecord)
        .where(MessageRecord.epoch_id.is_(None))
        .order_by(MessageRecord.sequence_number)
    )
    pending = result.scalars().all()
    if len(pending) < settings.anchor_batch_size:
        return
    await _anchor_batch(db, pending[:settings.anchor_batch_size])

async def _anchor_batch(db: AsyncSession, records: list):
    leaves = [r.payload_hash for r in records]
    root = merkle_root(leaves)
    first_seq = records[0].sequence_number
    last_seq  = records[-1].sequence_number
    receipt_str = await submit_anchor(root, first_seq, last_seq)
    epoch = Epoch(
        merkle_root=root,
        anchor_timestamp=receipt_str,
        first_seq=first_seq,
        last_seq=last_seq,
        closed=True,
    )
    db.add(epoch)
    await db.flush()
    for i, record in enumerate(records):
        _, proof = inclusion_proof(leaves, i)
        await db.execute(
            update(MessageRecord)
            .where(MessageRecord.id == record.id)
            .values(epoch_id=epoch.id, merkle_proof=json.dumps(proof))
        )
    await db.commit()

async def get_proof(db: AsyncSession, sequence_number: int) -> dict | None:
    result = await db.execute(
        select(MessageRecord).where(MessageRecord.sequence_number == sequence_number)
    )
    record = result.scalar_one_or_none()
    if not record or record.epoch_id is None:
        return None
    epoch_result = await db.execute(select(Epoch).where(Epoch.id == record.epoch_id))
    epoch = epoch_result.scalar_one_or_none()
    if not epoch:
        return None
    return {
        "sequence_number": sequence_number,
        "payload_hash": record.payload_hash,
        "merkle_proof": json.loads(record.merkle_proof),
        "merkle_root": epoch.merkle_root,
        "anchor_topic_id": settings.anchor_topic_id,
        "epoch_id": epoch.id,
        "epoch_range": {"first": epoch.first_seq, "last": epoch.last_seq},
        "anchor_timestamp": epoch.anchor_timestamp,
    }