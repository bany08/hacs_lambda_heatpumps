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


    return True

async def async_unload_entry(hass, config_entry):
    """Entferne die Integration."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)
    return unload_ok





# async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
#     """Set up the Lambda Heatpumps component."""
#     hass.data.setdefault(DOMAIN, {})
#     return True

# async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Set up Lambda Heatpumps from a config entry."""
#     hass.data[DOMAIN][entry.entry_id] = entry.data

#     # Forward the setup to the sensor platform
#     await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

#     # Read the software version from Modbus
#     client = ModbusTcpClient(
#         host=entry.data[CONF_MODBUS_HOST],
#         port=entry.data[CONF_MODBUS_PORT]
#     )
#     if client.connect():
#         result = client.read_holding_registers(200, 1, unit=entry.data[CONF_SLAVE_ID])  # Beispielregister für SW-Version
#         if not result.isError():
#             sw_version = result.registers[0]
#         else:
#             sw_version = "unknown"
#         client.close()
#     else:
#         sw_version = "unknown"

#     # Add device registry information
#     device_registry = dr.async_get(hass)

#     language = hass.config.language
#     translations = await async_get_translations(hass, language, "lambda_heatpumps")
#     # name = translations.get("device_name", "Lambda Heatpump 123")
#     name = translations.get("device_name", "Lambda Heatpump")

#     device_registry.async_get_or_create(
#         config_entry_id=entry.entry_id,
#         identifiers={(DOMAIN, entry.entry_id)},
#         name=name,
#         manufacturer=MANUFACTURER,
#         model=entry.data[CONF_MODEL],
#         #sw_version=str(sw_version)
#     )

#     return True

# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
#     """Unload a config entry."""
#     await hass.config_entries.async_forward_entry_unload(entry, "sensor")
#     hass.data[DOMAIN].pop(entry.entry_id)
#     return True
