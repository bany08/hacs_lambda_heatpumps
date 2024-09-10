from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from pymodbus.client import ModbusTcpClient

from .const import *

async def async_setup_entry(hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback):
    host = entry.data[CONF_MODBUS_HOST]
    port = entry.data[CONF_MODBUS_PORT]
    slave = entry.data[CONF_SLAVE_ID]
    language = hass.config.language

    client = ModbusTcpClient(host=host, port=port)
    
    async_add_entities([LambdaClimate(client, slave, language)], True)

class LambdaClimate(ClimateEntity):
    def __init__(self, client, slave, language="en"):
        self._client = client
        self._slave = slave
        self._target_temperature = None
        self._current_temperature = None
        self._hvac_mode = None
        self._language = language

    @property
    def name(self):
        return get_translation("Lambda Wärmepumpe", self._language)

    @property
    def supported_features(self):
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def hvac_modes(self):
        return [HVACMode.AUTO, HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF]

    @property
    def current_temperature(self):
        return self._current_temperature

    @property
    def target_temperature(self):
        return self._target_temperature