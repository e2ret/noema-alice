"""Мост к Home Assistant: STT, Assist (conversation) и TTS через REST API HA."""
from __future__ import annotations

import logging
import os

import httpx
import numpy as np

from .audio import ASR_RATE, decode_to_pcm

log = logging.getLogger("ha")

HA_URL = os.environ.get("HA_URL", "http://192.168.1.111:8123").rstrip("/")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
HA_STT = os.environ.get("HA_STT", "stt.vosk")
HA_TTS = os.environ.get("HA_TTS", "tts.piper")
HA_LANG = os.environ.get("HA_LANG", "ru")
HA_AGENT = os.environ.get("HA_AGENT", "")  # пусто — агент по умолчанию (встроенный Assist)

_H = {"Authorization": f"Bearer {HA_TOKEN}"}
_conv: dict[str, str] = {}


def stt_sync(pcm: np.ndarray) -> str:
    raw = (np.clip(pcm, -1, 1) * 32767).astype("<i2").tobytes()
    hdr = f"format=wav; codec=pcm; sample_rate={ASR_RATE}; bit_rate=16; channel=1; language={HA_LANG}"
    r = httpx.post(f"{HA_URL}/api/stt/{HA_STT}", headers={**_H, "X-Speech-Content": hdr}, content=raw, timeout=60)
    r.raise_for_status()
    j = r.json()
    return (j.get("text") or "").strip() if j.get("result") == "success" else ""


async def converse(device_id: str, text: str) -> str:
    body = {"text": text, "language": HA_LANG}
    if HA_AGENT:
        body["agent_id"] = HA_AGENT
    if device_id in _conv:
        body["conversation_id"] = _conv[device_id]
    async with httpx.AsyncClient(timeout=30) as cl:
        r = await cl.post(f"{HA_URL}/api/conversation/process", headers=_H, json=body)
        r.raise_for_status()
        j = r.json()
    if j.get("conversation_id"):
        _conv[device_id] = j["conversation_id"]
    speech = (((j.get("response") or {}).get("speech") or {}).get("plain") or {}).get("speech") or ""
    log.info("HA: %r -> %r", text, speech)
    return speech


async def tts_pcm(text: str) -> tuple[np.ndarray, int]:
    async with httpx.AsyncClient(timeout=60) as cl:
        r = await cl.post(f"{HA_URL}/api/tts_get_url", headers=_H, json={"engine_id": HA_TTS, "message": text})
        r.raise_for_status()
        j = r.json()
        path = j.get("path") or httpx.URL(j["url"]).raw_path.decode()
        a = await cl.get(HA_URL + path, headers=_H)
        a.raise_for_status()
    import asyncio
    return await asyncio.to_thread(decode_to_pcm, a.content), 48000
