import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import ConfigEntryNotReady
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

        return self.async_show_form(
            step_id="user",
            data_schema=self.get_config_schema(),
            errors=errors,
        )


    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LambdaHeatpumpsOptionsFlow(config_entry)
    
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

    def get_config_schema(self):
        model_options = ["EU8L", "EU10L", "EU13L", "EU15L", "EU20L"]
        return vol.Schema({
            vol.Required(CONF_MODBUS_HOST): str,
            vol.Required(CONF_MODBUS_PORT, default=DEFAULT_PORT): int,
            vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): int,
            vol.Required(CONF_MODEL): vol.In(model_options),
            vol.Required(CONF_AMOUNT_OF_HEATPUMPS, default=1): int,
            vol.Required(CONF_AMOUNT_OF_BOILERS, default=1): int,
            vol.Required(CONF_AMOUNT_OF_BUFFERS, default=1): int,
            vol.Required(CONF_AMOUNT_OF_SOLAR, default=0): int,
            vol.Required(CONF_AMOUNT_OF_HEAT_CIRCUITS, default=1): int,
        })

class LambdaHeatpumpsOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        _LOGGER.debug("LambdaHeatpumpsOptionsFlow initialized")

    async def async_step_init(self, user_input=None):
        _LOGGER.debug(f"async_step_init called with user_input: {user_input}")
        if user_input is not None:
            _LOGGER.debug("Processing user input")
            # Überprüfen Sie, ob sich Host oder Slave-ID geändert haben
            if (user_input[CONF_MODBUS_HOST] != self.config_entry.data[CONF_MODBUS_HOST] or
                user_input[CONF_SLAVE_ID] != self.config_entry.data[CONF_SLAVE_ID]):
                # Testen Sie die neue Verbindung
                try:
                    await self.hass.async_add_executor_job(
                        self.test_connection,
                        user_input[CONF_MODBUS_HOST],
                        self.config_entry.data[CONF_MODBUS_PORT],
                        user_input[CONF_SLAVE_ID],
                    )
                except ConnectionException:
                    return self.async_abort(reason="cannot_connect")
                except ValueError:
                    return self.async_abort(reason="invalid_slave_id")
                
                # Wenn die Verbindung erfolgreich war, aktualisieren Sie die Konfiguration
                new_data = {**self.config_entry.data, **user_input}
                self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
                return self.async_abort(reason="restart_required")
            
            return self.async_create_entry(title="", data=user_input)

        _LOGGER.debug("Showing form")
        schema = self.get_options_schema()
        return self.async_show_form(step_id="init", data_schema=schema)

    def get_options_schema(self):
        return vol.Schema({
            vol.Required(CONF_MODBUS_HOST, default=self.config_entry.data[CONF_MODBUS_HOST]): str,
            vol.Required(CONF_SLAVE_ID, default=self.config_entry.data[CONF_SLAVE_ID]): int,
            vol.Required(CONF_AMOUNT_OF_HEATPUMPS, default=self.config_entry.options.get(CONF_AMOUNT_OF_HEATPUMPS, 1)): int,
            vol.Required(CONF_AMOUNT_OF_BOILERS, default=self.config_entry.options.get(CONF_AMOUNT_OF_BOILERS, 1)): int,
            vol.Required(CONF_AMOUNT_OF_BUFFERS, default=self.config_entry.options.get(CONF_AMOUNT_OF_BUFFERS, 1)): int,
            vol.Required(CONF_AMOUNT_OF_SOLAR, default=self.config_entry.options.get(CONF_AMOUNT_OF_SOLAR, 0)): int,
            vol.Required(CONF_AMOUNT_OF_HEAT_CIRCUITS, default=self.config_entry.options.get(CONF_AMOUNT_OF_HEAT_CIRCUITS, 1)): int,
        })

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