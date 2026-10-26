"""Мастер добавления NOEMA Alice: адрес моста -> выбор колонки."""
from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_DEVICE_ID, CONF_SERVER, DEFAULT_SERVER, DOMAIN


class NoemaAliceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._server = DEFAULT_SERVER
        self._name = "Алиса"
        self._devices: list[str] = []

    async def _fetch_devices(self, server: str) -> list[str]:
        s = async_get_clientsession(self.hass)
        async with s.get(f"{server}/_status", timeout=aiohttp.ClientTimeout(total=10)) as r:
            r.raise_for_status()
            j = await r.json(content_type=None)
        ids = list((j.get("connections") or {}).keys())
        for d in j.get("devices") or []:
            if isinstance(d, dict) and d.get("id") and d["id"] not in ids:
                ids.append(d["id"])
        return ids

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            self._server = user_input[CONF_SERVER].rstrip("/")
            self._name = user_input[CONF_NAME]
            try:
                self._devices = await self._fetch_devices(self._server)
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                if not self._devices:
                    errors["base"] = "no_devices"
                elif len(self._devices) == 1:
                    return await self._create(self._devices[0])
                else:
                    return await self.async_step_device()
        schema = vol.Schema({
            vol.Required(CONF_SERVER, default=self._server): str,
            vol.Required(CONF_NAME, default=self._name): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_device(self, user_input=None):
        if user_input is not None:
            return await self._create(user_input[CONF_DEVICE_ID])
        schema = vol.Schema({vol.Required(CONF_DEVICE_ID): vol.In(self._devices)})
        return self.async_show_form(step_id="device", data_schema=schema)

    async def _create(self, device_id: str):
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=self._name,
            data={CONF_SERVER: self._server, CONF_DEVICE_ID: device_id, CONF_NAME: self._name},
        )
