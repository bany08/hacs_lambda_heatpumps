import logging
import voluptuous as vol
from homeassistant import config_entries
# from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import ConfigEntryNotReady
# from homeassistant.helpers.translation import async_get_translations
# from homeassistant.components.persistent_notification import create as persistent_notification_create
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException

from .const import DOMAIN, CONF_MODBUS_HOST, CONF_MODBUS_PORT, CONF_SLAVE_ID, DEFAULT_PORT, DEFAULT_SLAVE_ID, CONF_MODEL, CONF_AMOUNT_OF_HEATPUMPS, CONF_AMOUNT_OF_BOILERS, CONF_AMOUNT_OF_BUFFERS, CONF_AMOUNT_OF_SOLAR, CONF_AMOUNT_OF_HEAT_CIRCUITS

_LOGGER = logging.getLogger(__name__)

class LambdaHeatpumpsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(
                    self.test_connection,
                    user_input[CONF_MODBUS_HOST],
                    user_input[CONF_MODBUS_PORT],
                    user_input[CONF_SLAVE_ID],
                )
                await self.async_set_unique_id(f"{user_input[CONF_MODBUS_HOST]}:{user_input[CONF_MODBUS_PORT]}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Lambda Wärmepumpe ({user_input[CONF_MODEL]})",
                    data=user_input,
                )
            except ConnectionException:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_slave_id"
            except Exception as e:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        model_options = ["EU8L", "EU13L", "EU15L", "EU20L"]
        data_schema = vol.Schema(
            {
                vol.Required(CONF_MODBUS_HOST): str,
                vol.Required(CONF_MODBUS_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): int,
                vol.Required(CONF_MODEL): vol.In(model_options),
                vol.Required(CONF_AMOUNT_OF_HEATPUMPS, default=1): int,
                vol.Required(CONF_AMOUNT_OF_BOILERS, default=1): int,
                vol.Required(CONF_AMOUNT_OF_BUFFERS, default=1): int,
                vol.Required(CONF_AMOUNT_OF_SOLAR, default=0): int,
                vol.Required(CONF_AMOUNT_OF_HEAT_CIRCUITS, default=1): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
    

    # async def async_step_user(self, user_input=None) -> FlowResult:
    #     errors = {}
    #     if user_input is not None:
    #         try:
    #             await self.hass.async_add_executor_job(
    #                 self.test_connection,
    #                 user_input[CONF_MODBUS_HOST],
    #                 user_input[CONF_MODBUS_PORT],
    #                 user_input[CONF_SLAVE_ID]
    #             )
    #             # client = ModbusTcpClient(
    #             #     host=user_input[CONF_MODBUS_HOST],
    #             #     port=user_input[CONF_MODBUS_PORT]
    #             # )
    #             if not client.connect():
    #                 self._logger.error("Verbindung zum Modbus-Client fehlgeschlagen")
    #                 errors["base"] = "cannot_connect"
    #             else:
    #                 self._logger.debug("Verbindung zum Modbus-Client hergestellt")
    #                 # Versuchen Sie, ein spezifisches Register der Lambda Wärmepumpe zu lesen
    #                 result = client.read_holding_registers(100, 1, unit=user_input[CONF_SLAVE_ID])
    #                 if result.isError():
    #                     self._logger.error("Fehler beim Lesen des Modbus-Registers")
    #                     errors["base"] = "invalid_slave_id"
    #                 else:
    #                     self._logger.debug("Modbus-Register erfolgreich gelesen: %s", result.registers[0])
    #                     await self.async_set_unique_id(f"{user_input[CONF_MODBUS_HOST]}:{user_input[CONF_MODBUS_PORT]}")
    #                     language = self.hass.config.language
    #                     translations = await async_get_translations(self.hass, language, "lambda_heatpumps")
    #                     # _LOGGER.debug(f"Translations: {translations}")
    #                     # title = f"{translations.get('config.device_name', 'Lambda Heatpumps')} {user_input['model']}"
    #                     model = user_input['model']
    #                     title = f"Lambda Wärmepumpe ({model})"
    #                     description = translations.get('config.success.description', "Configuration for {device_model} created.\n\nFollowing devices were found:\n\n{device_name}\n{model} ({manufacturer})\nArea")
    #                     persistent_notification_create(
    #                         self.hass,
    #                         description.format(
    #                             model=user_input['model'],
    #                             device_name=translations.get('config.device_name', 'Lambda Heatpump'),
    #                             device_model=user_input['model'],
    #                             manufacturer=translations.get('config.manufacturer', 'LAMBDA Wärmepumpen GmbH')
    #                         ),
    #                         # title=translations.get('config.success.title', 'Success!')
    #                     )
    #                     return self.async_create_entry(
    #                         # title="hier steht der Titel drin",
    #                         #title=f"Lambda Wärmepumpe1 ({model})",
    #                         title=title,
    #                         data={
    #                             CONF_MODBUS_HOST: user_input[CONF_MODBUS_HOST],
    #                             CONF_MODBUS_PORT: user_input[CONF_MODBUS_PORT],
    #                             CONF_SLAVE_ID: user_input[CONF_SLAVE_ID],
    #                             "model": user_input[CONF_MODEL],
    #                             "amount_of_heatpumps": user_input[CONF_AMOUNT_OF_HEATPUMPS],
    #                             "amount_of_boilers": user_input[CONF_AMOUNT_OF_BOILERS],
    #                             "amount_of_buffers": user_input[CONF_AMOUNT_OF_BUFFERS],
    #                             "amount_of_solar": user_input[CONF_AMOUNT_OF_SOLAR],
    #                             "amount_of_heat_circuits": user_input[CONF_AMOUNT_OF_HEAT_CIRCUITS]
    #                         }
    #                     )
    #         except ConnectionException:
    #             self._logger.error("ConnectionException aufgetreten")
    #             errors["base"] = "cannot_connect"
    #         except Exception as e:
    #             self._logger.error(f"Unerwarteter Fehler: {e}")
    #         finally:
    #             client.close()

    #     # Lade Übersetzungen
    #     language = self.hass.config.language
    #     translations = await async_get_translations(self.hass, language, "lambda_heatpumps")

    #     # Definiere das Dropdown-Menü für das Modell
    #     model_options = ["EU8L", "EU13L", "EU15L", "EU20L"]

    #     return self.async_show_form(
    #         step_id="user",
    #         data_schema=vol.Schema(
    #             {
    #                 vol.Required(CONF_MODBUS_HOST): str,
    #                 vol.Required(CONF_MODBUS_PORT, default=DEFAULT_PORT): int,
    #                 vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): int,
    #                 vol.Required("model"): vol.In(model_options),
    #                 vol.Required(CONF_AMOUNT_OF_HEATPUMPS, default=1): int,
    #                 vol.Required(CONF_AMOUNT_OF_BOILERS, default=1): int,
    #                 vol.Required(CONF_AMOUNT_OF_BUFFERS, default=1): int,
    #                 vol.Required(CONF_AMOUNT_OF_SOLAR, default=0): int,
    #                 vol.Required(CONF_AMOUNT_OF_HEAT_CIRCUITS, default=1): int
    #             }
    #         ),

            # description_placeholders={
            #     "modbus_host": translations.get("config.step.user.data.modbus_host", "Modbus Host"),
            #     "modbus_port": translations.get("config.step.user.data.modbus_port", "Modbus Port"),
            #     "slave_id": translations.get("config.step.user.data.slave_id", "Slave ID"),
            #     "model": translations.get("config.step.user.data.model", "Model"),
            #     "amount_of_heatpumps": translations.get("config.step.user.data.amount_of_heatpumps", "Amount of Heatpumps"),
            #     "amount_of_boilers": translations.get("config.step.user.data.amount_of_boilers", "Amount of Boilers"),
            #     "amount_of_buffers": translations.get("config.step.user.data.amount_of_buffers", "Amount of Buffers"),
            #     "amount_of_solar": translations.get("config.step.user.data.amount_of_solar", "Amount of Solar thermal systems"),
            #     "amount_of_heat_circuits": translations.get("config.step.user.data.amount_of_heat_circuits", "Amount of Heat Circuits")
            # },
            # errors=errors,
        # )
    
    def test_connection(self, host, port, slave_id):
        """Test the connection to the Modbus device."""
        client = ModbusTcpClient(host=host, port=port)
        try:
            if not client.connect():
                raise ConnectionException("Cannot connect to Modbus client")
            result = client.read_holding_registers(100, 1, unit=slave_id)
            if result.isError():
                raise ValueError("Invalid slave ID")
        finally:
            client.close()
