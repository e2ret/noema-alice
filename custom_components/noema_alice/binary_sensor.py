"""Датчики: мост отвечает, колонка подключена к мосту."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, DOMAIN
from .coordinator import NoemaAliceCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: NoemaAliceCoordinator = hass.data[DOMAIN][entry.entry_id]
    dev = entry.data[CONF_DEVICE_ID]
    async_add_entities([BridgeSensor(coordinator, dev), StationSensor(coordinator, dev)])


class _Base(CoordinatorEntity[NoemaAliceCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _key = ""

    def __init__(self, coordinator: NoemaAliceCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"noema_alice_{device_id}_{self._key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})

    @property
    def available(self) -> bool:
        return True  # «выкл» и есть состояние, а не недоступность


class BridgeSensor(_Base):
    _key = "bridge"
    _attr_name = "Мост"

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success


class StationSensor(_Base):
    _key = "station"
    _attr_name = "Колонка на связи"

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success and bool((self.coordinator.data or {}).get("station"))
