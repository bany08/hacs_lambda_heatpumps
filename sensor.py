import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import *

_LOGGER = logging.getLogger(__name__)

class LambdaBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, name, register, model,  factor=1, config_entry_id=None, language="en"):
        """Initialisiere den Sensor."""
        super().__init__(coordinator)  # Verlinkung mit dem Coordinator
        self._name = name
        self._register = register
        self._state = None
        self._config_entry_id = config_entry_id
        self._model = model
        self._factor = factor
          # Lade die Zustände basierend auf der Sprache


        # Füge das Register dem Coordinator hinzu
        self.coordinator.add_register(self._register)
    @property
    def name(self):
        return self._name

    @property
    def state(self):
        """Hole den Zustand vom Coordinator."""
        value = self.coordinator.data.get(f"register_{self._register}")
        #_LOGGER.debug(f"Sensor {self._name} - Register {self._register} - Wert: {value}")
    
        if value is None:
            return None  # Gib None zurück, wenn kein Wert verfügbar ist
    
        return value * self._factor  # Multipliziere den Wert nur, wenn er nicht None ist


    @property
    def unique_id(self):
        return f"lambda_{self.coordinator.host}_{self.coordinator.port}_{self.coordinator.slave_id}_{self._register}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._config_entry_id)},
            "name": "Lambda Wärmepumpe",
            "manufacturer": MANUFACTURER,
            "model": self._model,
            "via_device": (DOMAIN, self._config_entry_id),
        }

    async def async_update(self):
        """Der Coordinator übernimmt das Update."""
        # _LOGGER.debug(f"Sensor {self._name} - async_update aufgerufen")
        await self.coordinator.async_request_refresh()

class LambdaErrorSensor(LambdaBaseSensor):
    @property
    def device_class(self):
        return "problem"  # Für Fehler-Sensoren

    @property
    def icon(self):
        return "mdi:alert-circle-outline"

class LambdaStateSensor(LambdaBaseSensor):
    def __init__(self, coordinator, name, register, model, states, config_entry_id=None, language="en"):
        super().__init__(coordinator, name, register, model, config_entry_id=config_entry_id, language=language)
        # self._states = states
        self._states = get_operating_states(language)

    @property
    def state(self):
        """Gibt den Zustand basierend auf dem Mapping der Zustände zurück."""
        if self.coordinator.data is not None:
            value = self.coordinator.data.get(f"register_{self._register}")
            # _LOGGER.debug(f"Sensor {self._name} - Register {self._register} - Wert: {value}")
            # _LOGGER.debug(f"Sensor {self._name} - States: {self._states}")
            if value is not None and value in self._states:
                return self._states[value]
        return None # or value
    
    @property
    def device_class(self):
        return "state"  # Für Zustands-Sensoren

    @property
    def icon(self):
        return "mdi:state-machine"

class LambdaTemperaturSensor(LambdaBaseSensor): 
    @property
    def state(self):
        """Hole den Wert vom Coordinator und wandle ihn in °C um."""
        if self.coordinator.data is not None:
            value = self.coordinator.data.get(f"register_{self._register}")
            # _LOGGER.debug(f"Sensor {self._name} - Register {self._register} - Wert: {value}")
            # _LOGGER.debug(f"Sensor {self._name} - Factor: {self._factor}")
            return value * self._factor if value is not None else None
        return None

    @property
    def unit_of_measurement(self):
        return "°C"
    
    @property
    def device_class(self):
        return "temperature"  # Für Temperatur-Sensoren


    @property
    def icon(self):
        return "mdi:thermometer"

class LambdaPowerSensor(LambdaBaseSensor):
    def __init__(self, coordinator, name, register, model, factor=1, unit="W", config_entry_id=None, language="en"):
        super().__init__(coordinator, name, register, model, factor=factor, config_entry_id=config_entry_id, language=language)
        self._unit = unit

    @property
    def state(self):
        """Hole den Wert vom Coordinator und wandle ihn entsprechend des Faktors um."""
        if self.coordinator.data is not None:
            value = self.coordinator.data.get(f"register_{self._register}")
            # _LOGGER.debug(f"Sensor {self._name} - Register {self._register} - Wert: {value}")
            # _LOGGER.debug(f"Sensor {self._name} - Factor: {self._factor}")
            return value * self._factor if value is not None else None
        return None

    @property
    def unit_of_measurement(self):
        return self._unit
    
    @property
    def device_class(self):
        return "power"  # Für Leistungssensoren

    @property
    def icon(self):
        return "mdi:flash"

class LambdaFlowSensor(LambdaBaseSensor):
    @property
    def state(self):
        """Hole den Volumenstrom-Wert und wandle ihn um."""
        if self.coordinator.data is not None:
            value = self.coordinator.data.get(f"register_{self._register}")
            # _LOGGER.debug(f"Sensor {self._name} - Register {self._register} - Wert: {value}")
            # _LOGGER.debug(f"Sensor {self._name} - Factor: {self._factor}")
            return value * self._factor if value is not None else None
        return None

    @property
    def unit_of_measurement(self):
        return "m³/h"
    
    @property
    def device_class(self):
        return "flow"  # Für Volumenstrom-Sensoren

    @property
    def icon(self):
        return "mdi:pump"


class LambdaPercentageSensor(LambdaBaseSensor):
    @property
    def state(self):
        """Hole den Zustand vom Coordinator."""
        # Greife auf die vom Coordinator abgerufenen Daten zu
        value = self.coordinator.data.get(f"register_{self._register}")
    
        if value is None:
            return None  # Gib None zurück, wenn der Wert nicht verfügbar ist
    
        return value * self._factor  # Führe die Multiplikation nur durch, wenn ein Wert vorhanden ist

    @property
    def state(self):
        """Hole den Prozentsatz und wandle ihn um."""
        if self.coordinator.data is not None:
            value = self.coordinator.data.get(f"register_{self._register}")
            # _LOGGER.debug(f"Sensor {self._name} - Register {self._register} - Wert: {value}")
            # _LOGGER.debug(f"Sensor {self._name} - Factor: {self._factor}")
            return value * self._factor if value is not None else None
        return None

    @property
    def unit_of_measurement(self):
            return "%"
    
    @property
    def device_class(self):
        return "percentage"  # Für Prozentsatz-Sensoren

    @property
    def icon(self):
        return "mdi:percent"





async def async_setup_entry(hass, entry, async_add_entities):
    """Setzt die Sensoren und den Coordinator auf."""
    _LOGGER.debug("async_setup_entry aufgerufen")

    # Hole den Coordinator aus der Registrierung
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Definiere die Sensoren
    sensors = [
        LambdaErrorSensor(coordinator, "Fehler Nummer", GENERAL_AMBIENT_ERROR_NUMBER, entry.data[CONF_MODEL]),
        LambdaErrorSensor(coordinator, "E-Manager Fehler Nummer", E_MANAGER_ERROR_NUMBER, entry.data[CONF_MODEL]),
        LambdaStateSensor(coordinator, "Betriebszustand", GENERAL_AMBIENT_OPERATING_STATE, entry.data[CONF_MODEL], get_operating_states()),
        LambdaTemperaturSensor(coordinator, "Aktuelle Umgebungstemperatur", GENERAL_AMBIENT_ACTUAL_AMBIENT_TEMP, entry.data[CONF_MODEL], 0.1),
        LambdaPowerSensor(coordinator, "Wärmepumpe 1 Leistungsaufnahme", HEATPUMP_1_FREQUENCY_INVERTER_ACTUAL_POWER_CONSUMPTION, entry.data[CONF_MODEL], 1),
        LambdaPowerSensor(coordinator, "Wärmepumpe 1 Heizleistung", HEATPUMP_1_ACTUAL_HEATING_CAPACITY, entry.data[CONF_MODEL], 1),
        LambdaFlowSensor(coordinator, "Volumenstrom", HEATPUMP_1_VOLUME_FLOW_HEAT_SINK, entry.data[CONF_MODEL], 0.01),
        LambdaPercentageSensor(coordinator, "COP", HEATPUMP_1_COEFFICIENT_OF_PERFORMANCE, entry.data[CONF_MODEL], 0.01),
    ]

    async_add_entities(sensors)

# Weitere Sensor-Klassen wie LambdaTemperaturSensor, LambdaPowerSensor, etc. können ähnlich angepasst werden.



# import logging
# from homeassistant.components.sensor import SensorEntity
# from homeassistant.core import HomeAssistant
# from homeassistant.helpers.entity_platform import AddEntitiesCallback
# from homeassistant.helpers.typing import ConfigType
# from homeassistant.helpers.translation import async_get_translations
# from pymodbus.client import ModbusTcpClient

# from .const import *

# _LOGGER = logging.getLogger(__name__)

# class LambdaBaseSensor(SensorEntity):
#     def __init__(self, name, register, model, language="en", config_entry_id=None):
#         self._name = name
#         self._register = register
#         self._state = None
#         self._language = language
#         self._config_entry_id = config_entry_id
#         self._model = model
#         self._hass = None

#     async def async_added_to_hass(self):
#         self._hass = self.hass

#     @property
#     def name(self):
#         return self._name

#     @property
#     def state(self):
#         return self._state

#     @property
#     def unique_id(self):
#         return f"lambda_{CONF_MODBUS_HOST}_{CONF_MODBUS_PORT}_{CONF_SLAVE_ID}_{self._register}"

#     @property
#     def device_info(self):
#         return {
#             "identifiers": {(DOMAIN, self._config_entry_id)},
#             "name": "Lambda Wärmepumpe",
#             "manufacturer": MANUFACTURER,
#             "model": self._model,
#             "via_device": (DOMAIN, self._config_entry_id)
#         }



#     async def async_update(self):
#         try:
#             _LOGGER.debug(f"LAMBDA HOST {entry.data[CONF_MODBUS_HOST]}, PORT {entry.data[CONF_MODBUS_PORT]}, SLAVE {entry.data[CONF_SLAVE_ID]}, REGISTER {self._register}")
#             client = ModbusTcpClient(
#                 host=CONF_MODBUS_HOST,
#                 port=CONF_MODBUS_PORT
#             )
#             result = client.read_holding_registers(self._register, 1, unit=CONF_SLAVE_ID)
#             _LOGGER.debug(f"Sensor {self._name} updated with state {self._state}")
#             if not result.isError():
#                 self._state = result.registers[0]
#             else:
#                 self._state = None
#         except Exception as e:
#             self._state = None
#             print(f"Fehler beim Lesen des Modbus-Registers: {e}")

#     async def async_get_name(self):
#         if self._hass:
#             return await async_get_translation(self._hass, self._name, self._language)
#         return self._name

# class LambdaErrorSensor(LambdaBaseSensor):
#     @property
#     def icon(self):
#         return "mdi:alert-circle-outline"

# class LambdaStateSensor(LambdaBaseSensor):
#     def __init__(self, name, register, model, states, language="en", config_entry_id=None):
#         super().__init__(name, register, model, language, config_entry_id)
#         self._states = states

#     @property
#     def state(self):
#         if self._state is not None and self._states and str(self._state) in self._states:
#             return self._states[str(self._state)]
#         return self._state

#     @property
#     def icon(self):
#         return "mdi:state-machine"

# class LambdaTemperaturSensor(LambdaBaseSensor):
#     def __init__(self, name, register, model, factor, language="en", config_entry_id=None):
#         super().__init__(name, register, model, language, config_entry_id)
#         self._factor = factor

#     @property
#     def state(self):
#         if self._state is not None:
#             return self._state * self._factor
#         return self._state

#     @property
#     def unit_of_measurement(self):
#         return "°C"

#     @property
#     def icon(self):
#         return "mdi:thermometer"

# class LambdaPowerSensor(LambdaBaseSensor):
#     def __init__(self, name, register, model, factor=1, unit="W", language="en", config_entry_id=None):
#         super().__init__(name, register, model, language, config_entry_id)
#         self._factor = factor
#         self._unit = unit

#     @property
#     def state(self):
#         if self._state is not None:
#             return self._state * self._factor
#         return self._state

#     @property
#     def unit_of_measurement(self):
#         return self._unit

#     @property
#     def icon(self):
#         return "mdi:flash"

# class LambdaFlowSensor(LambdaBaseSensor):
#     def __init__(self, name, register, model, factor, language="en", config_entry_id=None):
#         super().__init__(name, register, model, language, config_entry_id)
#         self._factor = factor

#     @property
#     def state(self):
#         if self._state is not None:
#             return self._state * self._factor
#         return self._state

#     @property
#     def unit_of_measurement(self):
#         return "m³/h"

#     @property
#     def icon(self):
#         return "mdi:pump"

# class LambdaPercentageSensor(LambdaBaseSensor):
#     def __init__(self, name, register, model, factor, language="en", config_entry_id=None):
#         super().__init__(name, register, model, language, config_entry_id)
#         self._factor = factor

#     @property
#     def state(self):
#         if self._state is not None:
#             return self._state * self._factor
#         return self._state

#     @property
#     def unit_of_measurement(self):
#         return "%"

#     @property
#     def icon(self):
#         return "mdi:percent"



# async def async_setup_entry(hass: HomeAssistant, entry: ConfigType, async_add_entities: AddEntitiesCallback):
#     _LOGGER.debug("async_setup_entry aufgerufen")
#     language = hass.config.language
#     model = entry.data[CONF_MODEL]
        
#     extra_info = {
#         "amount_of_heatpumps": entry.data.get("heat_pumps", 1),
#         "amount_of_boilers": entry.data.get("boilers", 1),
#         "amount_of_buffers": entry.data.get("buffers", 1),
#         "amount_of_solar": entry.data.get("solar", 1),
#         "amount_of_heat_circuits": entry.data.get("heat_circuits", 1),
#     }
    
#     client = ModbusTcpClient(host=CONF_MODBUS_HOST, port=CONF_MODBUS_PORT)
    
#  # Sensoren in inhaltliche Sektionen aufteilen
#     generell_sensors = [
#         LambdaErrorSensor("Fehler Nummer", REGISTER_ERROR_NUMBER, model, config_entry_id=entry.entry_id),        
#         LambdaStateSensor("Betriebszustand", REGISTER_OPERATING_STATE, model, get_operating_states(), config_entry_id=entry.entry_id)
#     ]

#     energiemanager_sensors = [
#         LambdaErrorSensor("E-Manager Fehlernummer", REGISTER_EMANAGER_ERROR_NUMBER, model, config_entry_id=entry.entry_id)
#     ]

#     brauchwasser_sensors = [
#         LambdaTemperaturSensor("Aktuelle Umgebungstemperatur", REGISTER_ACTUAL_AMBIENT_TEMP, model, 0.1, config_entry_id=entry.entry_id),
#         LambdaTemperaturSensor("Durchschnittliche Umgebungstemperatur 1h", REGISTER_AVERAGE_AMBIENT_TEMP, model, 0.1, config_entry_id=entry.entry_id),
#         LambdaTemperaturSensor("Berechnete Umgebungstemperatur", REGISTER_CALCULATED_AMBIENT_TEMP, model, 0.1, config_entry_id=entry.entry_id)
#     ]

#     heizung_sensors = [
#         LambdaFlowSensor("Kühlkörper Volumenstrom", REGISTER_HP1_VOL_SINK, model, 0.01, config_entry_id=entry.entry_id),
#         LambdaPercentageSensor("COP", REGISTER_COP, model, 0.01, config_entry_id=entry.entry_id)
#     ]

#     # Alle Sensoren zusammenführen
#     sensors = generell_sensors + energiemanager_sensors + brauchwasser_sensors + heizung_sensors

#     # sensors = [
#     #     LambdaErrorSensor("Fehler Nummer", REGISTER_ERROR_NUMBER, language, config_entry_id=entry.entry_id),        
#     #     LambdaErrorSensor("E-Manager Fehlernummer", REGISTER_EMANAGER_ERROR_NUMBER, language, config_entry_id=entry.entry_id),
#     #     LambdaStateSensor("Betriebszustand", REGISTER_OPERATING_STATE, get_operating_states(language), language, config_entry_id=entry.entry_id),
#     #     LambdaTemperaturSensor("Aktuelle Umgebungstemperatur", REGISTER_ACTUAL_AMBIENT_TEMP, 0.1, language, config_entry_id=entry.entry_id),
#     #     LambdaTemperaturSensor("Durchschnittliche Umgebungstemperatur 1h", REGISTER_AVERAGE_AMBIENT_TEMP, 0.1, language, config_entry_id=entry.entry_id),
#     #     LambdaTemperaturSensor("Berechnete Umgebungstemperatur", REGISTER_CALCULATED_AMBIENT_TEMP, 0.1, language, config_entry_id=entry.entry_id),
#     #     LambdaFlowSensor("Kühlkörper Volumenstrom", REGISTER_HP1_VOL_SINK, 0.01, language, config_entry_id=entry.entry_id),
#     #     LambdaPercentageSensor("COP", REGISTER_COP, 0.01, language, config_entry_id=entry.entry_id)
#     # ]
    
#     _LOGGER.debug(f"Sensoren erstellt: {sensors}")
#     async_add_entities(sensors, True)
#     _LOGGER.debug("Sensoren hinzugefügt")
