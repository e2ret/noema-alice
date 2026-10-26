"""NOEMA Alice — Яндекс Станция как локальный голосовой спутник Home Assistant."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID, CONF_SERVER, DOMAIN
from .coordinator import NoemaAliceCoordinator

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = NoemaAliceCoordinator(hass, entry.data[CONF_SERVER], entry.data[CONF_DEVICE_ID])
    await coordinator.async_refresh()  # недоступный мост не должен ронять загрузку: датчик покажет «выкл»
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok
