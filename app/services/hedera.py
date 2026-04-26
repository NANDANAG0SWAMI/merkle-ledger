import json
import asyncio
from functools import partial
from hiero_sdk_python import Client, AccountId, PrivateKey, TopicId, TopicMessageSubmitTransaction
from app.config import settings

def _client() -> Client:
    client = Client()
    client.set_operator(
        AccountId.from_string(settings.operator_id),
        PrivateKey.from_string(settings.operator_key),
    )
    return client

def _submit_sync(topic_id: str, message: str) -> str:
    client = _client()
    key = PrivateKey.from_string(settings.operator_key)
    receipt = (
        TopicMessageSubmitTransaction()
        .set_topic_id(TopicId.from_string(topic_id))
        .set_message(message)
        .freeze_with(client)
        .sign(key)
        .execute(client)
    )
    return str(receipt)

async def submit_to_topic(topic_id: str, message: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_submit_sync, topic_id, message))

async def submit_message(payload: dict) -> str:
    return await submit_to_topic(settings.topic_id, json.dumps(payload))

async def submit_anchor(root: str, first_seq: int, last_seq: int) -> str:
    anchor = {"type": "merkle_anchor", "root": root, "first_seq": first_seq, "last_seq": last_seq}
    return await submit_to_topic(settings.anchor_topic_id, json.dumps(anchor))