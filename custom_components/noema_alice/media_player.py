"""Колонка как media_player: TTS, медиабраузер, радио, громкость."""
from __future__ import annotations

import asyncio

import aiohttp

from homeassistant.components import media_source
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature as F,
    MediaPlayerState,
)
from homeassistant.components.media_player.browse_media import async_process_play_media_url
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICE_ID, CONF_SERVER, DOMAIN

TEXT_TYPES = {"dialog", "text", "tts"}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    d = entry.data
    async_add_entities([NoemaAlicePlayer(d[CONF_SERVER], d[CONF_DEVICE_ID], d.get(CONF_NAME) or "Алиса")])


class NoemaAlicePlayer(MediaPlayerEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (F.PLAY_MEDIA | F.BROWSE_MEDIA | F.PLAY | F.PAUSE | F.STOP
                                | F.VOLUME_SET | F.NEXT_TRACK | F.PREVIOUS_TRACK)

    def __init__(self, server: str, device_id: str, name: str) -> None:
        self._server = server.rstrip("/")
        self._dev = device_id
        self._attr_unique_id = f"noema_alice_{device_id}"
        self._attr_state = MediaPlayerState.IDLE
        self._attr_volume_level = 0.5
        self._known_volume: float | None = None  # последняя громкость, заданная через HA
        self._restore_task: asyncio.Task | None = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=name,
            manufacturer="Yandex · NOEMA",
            model="Станция Мини (NOEMA Alice)",
            configuration_url=self._server + "/_docs",
        )

    async def _post(self, path: str, data: dict) -> None:
        s = async_get_clientsession(self.hass)
        async with s.post(f"{self._server}/{path}/{self._dev}", json=data,
                          timeout=aiohttp.ClientTimeout(total=15)) as r:
            r.raise_for_status()

    def _set(self, state: MediaPlayerState) -> None:
        self._attr_state = state
        self.async_write_ha_state()

    async def async_update(self) -> None:
        try:
            s = async_get_clientsession(self.hass)
            async with s.get(f"{self._server}/_status", timeout=aiohttp.ClientTimeout(total=5)) as r:
                j = await r.json(content_type=None)
            self._attr_available = bool((j.get("connections") or {}).get(self._dev))
        except Exception:  # noqa: BLE001
            self._attr_available = False

    async def _say(self, text: str, volume: float | None) -> None:
        """Озвучить текст; с volume громкость временно меняется и потом возвращается."""
        if self._restore_task:
            self._restore_task.cancel()
            self._restore_task = None
        prev = self._known_volume
        if volume is not None:
            await self._post("_cmd", {"command": "setVolume", "volume": round(volume, 2)})
            await asyncio.sleep(0.5)
        await self._post("_say", {"text": text})
        if volume is not None and prev is not None:
            self._restore_task = self.hass.async_create_task(self._restore_volume(prev, 3 + len(text) * 0.08))
        elif volume is not None:
            self._known_volume = volume
            self._attr_volume_level = volume
            self.async_write_ha_state()

    async def _restore_volume(self, volume: float, delay: float) -> None:
        # мост не знает, когда колонка договорила, поэтому ждём по длине текста
        await asyncio.sleep(delay)
        await self._post("_cmd", {"command": "setVolume", "volume": round(volume, 2)})

    async def async_play_media(self, media_type, media_id, **kwargs) -> None:
        if str(media_type).lower() in TEXT_TYPES:
            volume = (kwargs.get("extra") or {}).get("volume_level")
            await self._say(str(media_id), float(volume) if volume is not None else None)
            return
        if media_source.is_media_source_id(media_id):
            item = await media_source.async_resolve_media(self.hass, media_id, self.entity_id)
            media_id = item.url
        url = async_process_play_media_url(self.hass, media_id)
        title = (kwargs.get("extra") or {}).get("title") or ""
        await self._post("_play", {"url": url, "title": title})
        self._attr_media_title = title or None
        self._set(MediaPlayerState.PLAYING)

    async def async_browse_media(self, media_content_type=None, media_content_id=None):
        return await media_source.async_browse_media(
            self.hass, media_content_id,
            content_filter=lambda i: i.media_content_type.startswith("audio/"))

    async def async_media_play(self) -> None:
        await self._post("_cmd", {"command": "play"})
        self._set(MediaPlayerState.PLAYING)

    async def async_media_pause(self) -> None:
        await self._post("_cmd", {"command": "stop"})
        self._set(MediaPlayerState.PAUSED)

    async def async_media_stop(self) -> None:
        await self._post("_cmd", {"command": "stop"})
        self._set(MediaPlayerState.IDLE)

    async def async_media_next_track(self) -> None:
        await self._post("_cmd", {"command": "next"})

    async def async_media_previous_track(self) -> None:
        await self._post("_cmd", {"command": "prev"})

    async def async_set_volume_level(self, volume: float) -> None:
        await self._post("_cmd", {"command": "setVolume", "volume": round(volume, 2)})
        self._attr_volume_level = volume
        self._known_volume = volume
        self.async_write_ha_state()
