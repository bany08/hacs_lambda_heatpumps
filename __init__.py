import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import device_registry as dr
# from homeassistant.helpers.translation import async_get_translations
from pymodbus.client import ModbusTcpClient
from .coordinator import LambdaHeatpumpCoordinator

from .const import MANUFACTURER, DOMAIN, CONF_MODBUS_HOST, CONF_MODBUS_PORT, CONF_SLAVE_ID, CONF_MODEL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry):
    """Initialisiere die Integration mit einem config_entry."""
    # _LOGGER.debug(f"Config Entry: {config_entry.data}")  # Füge Logging hinzu, um die Konfigurationsdaten zu überprüfen
    # Überprüfen Sie, ob der Eintrag bereits eingerichtet wurde
    if config_entry.entry_id in hass.data.setdefault(DOMAIN, {}):
        return True
    
    # Konfigurationsparameter aus config_entry abrufen
    host = config_entry.data.get("modbus_host")
    port = config_entry.data.get("modbus_port")
    slave_id = config_entry.data.get("slave_id")

    # _LOGGER.debug(f"Host: {host}, Port: {port}, Slave ID: {slave_id}")  # Prüfe, ob die Werte korrekt sind

    # Erstellen eines Coordinators für die gemeinsame Datennutzung
    coordinator = LambdaHeatpumpCoordinator(hass, host, port, slave_id)

    # Der Coordinator muss gestartet werden
    await coordinator.async_config_entry_first_refresh()

    # Speichere den Coordinator in `hass.data`
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

    # Leite das Setup an die Sensor-Komponente weiter
    await hass.config_entries.async_forward_entry_setups(config_entry, ["sensor"])

    # Register the options flow
    config_entry.add_update_listener(async_update_options)

    return True

async def async_unload_entry(hass, config_entry):
    """Entferne die Integration."""
    # unload_ok = await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
    # if unload_ok:
    #     hass.data[DOMAIN].pop(config_entry.entry_id)
    # return unload_ok

    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok

async def async_reload_entry(hass, config_entry):
    """Reload config entry."""
    await async_unload_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)

async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)



