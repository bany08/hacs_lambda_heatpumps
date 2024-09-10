from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import device_registry as dr
from pymodbus.client import ModbusTcpClient

from .const import DOMAIN, CONF_MODBUS_HOST, CONF_MODBUS_PORT, CONF_SLAVE_ID, CONF_MODEL


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Lambda Heatpumps component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lambda Heatpumps from a config entry."""
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward the setup to the sensor platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    # Read the software version from Modbus
    client = ModbusTcpClient(
        host=entry.data[CONF_MODBUS_HOST],
        port=entry.data[CONF_MODBUS_PORT]
    )
    if client.connect():
        result = client.read_holding_registers(200, 1, unit=entry.data[CONF_SLAVE_ID])  # Beispielregister für SW-Version
        if not result.isError():
            sw_version = result.registers[0]
        else:
            sw_version = "unknown"
        client.close()
    else:
        sw_version = "unknown"

    # Add device registry information
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="Lambda Heatpump",
        manufacturer="Lambda",
        model=entry.data[CONF_MODEL],
        #sw_version=str(sw_version)
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
