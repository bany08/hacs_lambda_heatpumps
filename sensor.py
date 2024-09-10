import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.translation import async_get_translations
from pymodbus.client import ModbusTcpClient

from .const import *

_LOGGER = logging.getLogger(__name__)

class LambdaBaseSensor(SensorEntity):
    def __init__(self, name, host, port, client, slave, register, model, language="en", config_entry_id=None):
        self._name = name
        self._host = host
        self._port = port
        self._client = client
        self._slave = slave
        self._register = register
        self._state = None
        self._language = language
        self._config_entry_id = config_entry_id
        self._model = model
        self._hass = None

    async def async_added_to_hass(self):
        self._hass = self.hass

    @property
    def name(self):
        return f"lambda_{self._name}"

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return f"lambda_{self._host}_{self._port}_{self._slave}_{self._register}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry_id)},
            "name": "Lambda Wärmepumpe",
            "manufacturer": MANUFACTURER,
            "model": self._model,
        }

    async def async_update(self):
        try:
            result = self._client.read_holding_registers(self._register, 1, unit=self._slave)
            if not result.isError():
                self._state = result.registers[0]
            else:
                self._state = None
        except Exception as e:
            self._state = None
            print(f"Fehler beim Lesen des Modbus-Registers: {e}")

    async def async_get_name(self):
        if self._hass:
            return await async_get_translation(self._hass, self._name, self._language)
        return self._name

class LambdaErrorSensor(LambdaBaseSensor):
    @property
    def icon(self):
        return "mdi:alert-circle-outline"

class LambdaStateSensor(LambdaBaseSensor):
    def __init__(self, name, host, port, client, slave, register, model, states, language="en", config_entry_id=None):
        super().__init__(name, host, port, client, slave, register, model, language, config_entry_id)
        self._states = states

    @property
    def state(self):
        if self._state is not None and self._states and str(self._state) in self._states:
            return self._states[str(self._state)]
        return self._state

    @property
    def icon(self):
        return "mdi:state-machine"

class LambdaTemperaturSensor(LambdaBaseSensor):
    def __init__(self, name, host, port, client, slave, register, model, factor, language="en", config_entry_id=None):
        super().__init__(name, host, port, client, slave, register, model, language, config_entry_id)
        self._factor = factor

    @property
    def state(self):
        if self._state is not None:
            return self._state * self._factor
        return self._state

    @property
    def unit_of_measurement(self):
        return "°C"

    @property
    def icon(self):
        return "mdi:thermometer"

class LambdaPowerSensor(LambdaBaseSensor):
    def __init__(self, name, host, port, client, slave, register, model, factor=1, unit="W", language="en", config_entry_id=None):
        super().__init__(name, host, port, client, slave, register, model, language, config_entry_id)
        self._factor = factor
        self._unit = unit

    @property
    def state(self):
        if self._state is not None:
            return self._state * self._factor
        return self._state

    @property
    def unit_of_measurement(self):
        return self._unit

    @property
    def icon(self):
        return "mdi:flash"

class LambdaFlowSensor(LambdaBaseSensor):
    def __init__(self, name, host, port, client, slave, register, model, factor, language="en", config_entry_id=None):
        super().__init__(name, host, port, client, slave, register, model, language, config_entry_id)
        self._factor = factor

    @property
    def state(self):
        if self._state is not None:
            return self._state * self._factor
        return self._state

    @property
    def unit_of_measurement(self):
        return "m³/h"

    @property
    def icon(self):
        return "mdi:pump"

class LambdaPercentageSensor(LambdaBaseSensor):
    def __init__(self, name, host, port, client, slave, register, model, factor, language="en", config_entry_id=None):
        super().__init__(name, host, port, client, slave, register, model, language, config_entry_id)
        self._factor = factor

    @property
    def state(self):
        if self._state is not None:
            return self._state * self._factor
        return self._state

    @property
    def unit_of_measurement(self):
        return "%"

    @property
    def icon(self):
        return "mdi:percent"



async def async_setup_entry(hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("async_setup_entry aufgerufen")
    host = entry.data[CONF_MODBUS_HOST]
    port = entry.data[CONF_MODBUS_PORT]
    slave = entry.data[CONF_SLAVE_ID]
    language = hass.config.language
    model = entry.data["model"]
        
    extra_info = {
        "amount_of_heatpumps": entry.data.get("heat_pumps", 1),
        "amount_of_boilers": entry.data.get("boilers", 1),
        "amount_of_buffers": entry.data.get("buffers", 1),
        "amount_of_solar": entry.data.get("solar", 1),
        "amount_of_heat_circuits": entry.data.get("heat_circuits", 1),
    }
    
    client = ModbusTcpClient(host=host, port=port)
    
 # Sensoren in inhaltliche Sektionen aufteilen
    generell_sensors = [
        LambdaErrorSensor("Fehler Nummer", host, port, client, slave, REGISTER_ERROR_NUMBER, model,config_entry_id=entry.entry_id),        
        LambdaStateSensor("Betriebszustand", host, port, client, slave, REGISTER_OPERATING_STATE, model, get_operating_states(), config_entry_id=entry.entry_id)
    ]

    energiemanager_sensors = [
        LambdaErrorSensor("E-Manager Fehlernummer", host, port, client, slave, REGISTER_EMANAGER_ERROR_NUMBER, model, config_entry_id=entry.entry_id)
    ]

    brauchwasser_sensors = [
        LambdaTemperaturSensor("Aktuelle Umgebungstemperatur", host, port, client, slave, REGISTER_ACTUAL_AMBIENT_TEMP, model, 0.1, config_entry_id=entry.entry_id),
        LambdaTemperaturSensor("Durchschnittliche Umgebungstemperatur 1h", host, port, client, slave, REGISTER_AVERAGE_AMBIENT_TEMP, model, 0.1, config_entry_id=entry.entry_id),
        LambdaTemperaturSensor("Berechnete Umgebungstemperatur", host, port, client, slave, REGISTER_CALCULATED_AMBIENT_TEMP, model, 0.1, config_entry_id=entry.entry_id)
    ]

    heizung_sensors = [
        LambdaFlowSensor("Kühlkörper Volumenstrom", host, port, client, slave, REGISTER_HP1_VOL_SINK, model, 0.01, config_entry_id=entry.entry_id),
        LambdaPercentageSensor("COP", host, port, client, slave, REGISTER_COP, model, 0.01, config_entry_id=entry.entry_id)
    ]

    # Alle Sensoren zusammenführen
    sensors = generell_sensors + energiemanager_sensors + brauchwasser_sensors + heizung_sensors

    # sensors = [
    #     LambdaErrorSensor("Fehler Nummer", host, port, client, slave, REGISTER_ERROR_NUMBER, language, config_entry_id=entry.entry_id),        
    #     LambdaErrorSensor("E-Manager Fehlernummer", host, port, client, slave, REGISTER_EMANAGER_ERROR_NUMBER, language, config_entry_id=entry.entry_id),
    #     LambdaStateSensor("Betriebszustand", host, port, client, slave, REGISTER_OPERATING_STATE, get_operating_states(language), language, config_entry_id=entry.entry_id),
    #     LambdaTemperaturSensor("Aktuelle Umgebungstemperatur", host, port, client, slave, REGISTER_ACTUAL_AMBIENT_TEMP, 0.1, language, config_entry_id=entry.entry_id),
    #     LambdaTemperaturSensor("Durchschnittliche Umgebungstemperatur 1h", host, port, client, slave, REGISTER_AVERAGE_AMBIENT_TEMP, 0.1, language, config_entry_id=entry.entry_id),
    #     LambdaTemperaturSensor("Berechnete Umgebungstemperatur", host, port, client, slave, REGISTER_CALCULATED_AMBIENT_TEMP, 0.1, language, config_entry_id=entry.entry_id),
    #     LambdaFlowSensor("Kühlkörper Volumenstrom", host, port, client, slave, REGISTER_HP1_VOL_SINK, 0.01, language, config_entry_id=entry.entry_id),
    #     LambdaPercentageSensor("COP", host, port, client, slave, REGISTER_COP, 0.01, language, config_entry_id=entry.entry_id)
    # ]
    
    _LOGGER.debug("Sensoren erstellt: %s", sensors)
    async_add_entities(sensors, True)
    _LOGGER.debug("Sensoren hinzugefügt")






