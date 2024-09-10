from homeassistant.components.number import NumberEntity
from homeassistant.const import TEMP_CELSIUS
from pymodbus.client import ModbusTcpClient

from .const import *

class LambdaBaseNumber(NumberEntity):
    def __init__(self, name, client, slave, register, unit=None, language="en"):
        self._name = name
        self._client = client
        self._slave = slave
        self._register = register
        self._unit = unit
        self._value = None
        self._language = language

    @property
    def name(self):
        return get_translation(self._name, self._language)

    @property
    def value(self):
        return self._value

    @property
    def unit_of_measurement(self):
        return self._unit

    def set_value(self, value):
        try:
            result = self._client.write_register(self._register, int(value), unit=self._slave)
            if result.isError():
                print(f"Fehler beim Schreiben des Modbus-Registers: {result}")
            else:
                self._value = value
        except Exception as e:
            print(f"Fehler beim Schreiben des Modbus-Registers: {e}")

class LambdaTargetTemperatureNumber(LambdaBaseNumber):
    def __init__(self, name, client, slave, register, factor=1, language="en"):
        super().__init__(name, client, slave, register, TEMP_CELSIUS, language)
        self._factor = factor

    @property
    def value(self):
        return round(self._value * self._factor, 2) if self._value is not None else None

    def set_value(self, temperature):
        value = int(temperature / self._factor)
        super().set_value(value)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback):
    host = entry.data[CONF_MODBUS_HOST]
    port = entry.data[CONF_MODBUS_PORT]
    slave = entry.data[CONF_SLAVE_ID]
    language = hass.config.language

    client = ModbusTcpClient(host=host, port=port)
    
    numbers = [
        LambdaTargetTemperatureNumber("Zieltemperatur", client, slave, REGISTER_REQUEST_FLOW_LINE_TEMP, 0.1, language)
    ]

    async_add_entities(numbers, update_before_add=True)