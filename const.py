import json
from homeassistant.const import CONF_LANGUAGE


# Domain
DOMAIN = "lambda_heatpumps"


# Manufacturer
MANUFACTURER = "Lambda Wärmepumpen GmbH"

# Configuration
CONF_MODBUS_HOST = "modbus_host"
CONF_MODBUS_PORT = "modbus_port"
CONF_SLAVE_ID = "slave_id"
CONF_MODEL = "model"

DEFAULT_PORT = 502
DEFAULT_SLAVE_ID = 1



# Register definitions
# Modules:
# - General Ambient => GA
# - General E-Manager => EM
# - Heat pump (ModulNr. 1-3)
# - Boiler (ModulNr. 1-5)
# - Buffer (ModulNr. 1-5)
# - Solar (ModulNr. 1-2)

REGISTER_ERROR_NUMBER = 0
REGISTER_OPERATING_STATE = 1
REGISTER_ACTUAL_AMBIENT_TEMP = 2
REGISTER_AVERAGE_AMBIENT_TEMP = 3
REGISTER_CALCULATED_AMBIENT_TEMP = 4

REGISTER_EMANAGER_ERROR_NUMBER = 100
REGISTER_HP1_VOL_SINK = 1006
REGISTER_COP = 1013


async def async_get_translation(hass, key, language="en"):
    translations = await async_get_translations(hass, language, DOMAIN)
    return translations.get(key, key)


def get_operating_states(language="en"):
    # Beispielhafte Zustände, diese sollten entsprechend der tatsächlichen Zustände angepasst werden
    states = {
        0: "OFF",
        1: "AUTOMATIC",
        2: "MANUAL",
        3: "ERROR"
    }
    return states