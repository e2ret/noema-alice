"""Кнопка «Перезапустить мост»."""
from __future__ import annotations

import aiohttp

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEVICE_ID, CONF_SERVER, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([RestartBridgeButton(entry.data[CONF_SERVER], entry.data[CONF_DEVICE_ID])])


class RestartBridgeButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Перезапустить мост"
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(self, server: str, device_id: str) -> None:
        self._server = server.rstrip("/")
        self._attr_unique_id = f"noema_alice_{device_id}_restart"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    async def async_press(self) -> None:
        s = async_get_clientsession(self.hass)
        async with s.post(f"{self._server}/_restart", timeout=aiohttp.ClientTimeout(total=10)) as r:
            r.raise_for_status()
