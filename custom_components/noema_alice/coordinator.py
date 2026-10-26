"""Опрос моста: доступен ли он и подключена ли колонка."""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class NoemaAliceCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, server: str, device_id: str) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=10))
        self.server = server.rstrip("/")
        self.device_id = device_id

    async def _async_update_data(self) -> dict:
        s = async_get_clientsession(self.hass)
        try:
            async with s.get(f"{self.server}/_status", timeout=aiohttp.ClientTimeout(total=5)) as r:
                r.raise_for_status()
                j = await r.json(content_type=None)
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Мост не отвечает: {err}") from err
        cfg: dict = {}
        try:  # нет патча apply_config.py на мосту — просто нет выбора движков
            async with s.get(f"{self.server}/_config", timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    cfg = await r.json(content_type=None)
        except Exception:  # noqa: BLE001
            pass
        return {"station": bool((j.get("connections") or {}).get(self.device_id)),
                "tts": cfg.get("tts"), "stt": cfg.get("stt")}
