"""Выбор движков речи моста: синтез (TTS) и распознавание (STT)."""
from __future__ import annotations

import aiohttp

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, CONF_SERVER, DOMAIN
from .coordinator import NoemaAliceCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: NoemaAliceCoordinator = hass.data[DOMAIN][entry.entry_id]
    server, dev = entry.data[CONF_SERVER], entry.data[CONF_DEVICE_ID]
    async_add_entities([
        EngineSelect(coordinator, server, dev, "tts", "Движок речи"),
        EngineSelect(coordinator, server, dev, "stt", "Распознавание речи"),
    ])


class EngineSelect(CoordinatorEntity[NoemaAliceCoordinator], SelectEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: NoemaAliceCoordinator, server: str, device_id: str, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._server = server.rstrip("/")
        self._key = key  # он же домен сущностей HA: tts / stt
        self._attr_name = name
        self._attr_unique_id = f"noema_alice_{device_id}_{key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    @property
    def current_option(self) -> str | None:
        return (self.coordinator.data or {}).get(self._key)

    @property
    def options(self) -> list[str]:
        ids = sorted(self.hass.states.async_entity_ids(self._key))
        cur = self.current_option
        if cur and cur not in ids:
            ids.append(cur)
        return ids

    @property
    def available(self) -> bool:
        return super().available and self.current_option is not None

    async def async_select_option(self, option: str) -> None:
        s = async_get_clientsession(self.hass)
        async with s.post(f"{self._server}/_config", json={self._key: option},
                          timeout=aiohttp.ClientTimeout(total=10)) as r:
            r.raise_for_status()
        await self.coordinator.async_request_refresh()
