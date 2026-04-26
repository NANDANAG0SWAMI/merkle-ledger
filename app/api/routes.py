import re
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.hedera import submit_message
from app.services.anchoring import record_message, get_proof
from app.services.merkle import verify_proof
from app.db.session import get_db

router = APIRouter()

_seq_counter = 0  # fallback counter until SDK receipt parsing is fixed

@router.post("/log", status_code=202)
async def log_message(payload: dict, db: AsyncSession = Depends(get_db)):
    global _seq_counter
    try:
        receipt = await submit_message(payload)
        # Try to parse from receipt string, fall back to incrementing counter
        match = re.search(r'\d+', str(receipt))
        seq = int(match.group()) if match and int(match.group()) > 0 else None

        # If SDK gives us 0 or nothing, use our own counter
        if not seq:
            _seq_counter += 1
            seq = _seq_counter

        await record_message(db, seq, payload)
        return {"status": "submitted", "sequence_number": seq, "receipt": str(receipt)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/proof/{sequence_number}")
async def get_inclusion_proof(sequence_number: int, db: AsyncSession = Depends(get_db)):
    proof = await get_proof(db, sequence_number)
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not available yet — batch not anchored")
    return proof

@router.post("/verify")
async def verify_inclusion(body: dict):
    try:
        index = body["sequence_number"] - body["epoch_range"]["first"]
        valid = verify_proof(
            leaf=body["payload_hash"],
            proof=body["merkle_proof"],
            root=body["merkle_root"],
            index=index,
        )
        return {"valid": valid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health")
async def health():
    return {"status": "ok"}