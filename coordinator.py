from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from datetime import timedelta
import logging

_LOGGER = logging.getLogger(__name__)

class LambdaHeatpumpCoordinator(DataUpdateCoordinator):
    """Koordinator für LambdaHeatpump-Datenabfragen."""

    def __init__(self, hass, host, port, slave_id):
        """Initialisiere den Coordinator."""
        self.hass = hass
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self._registers_to_read = {}
        self._client = None

        # _LOGGER.debug(f"Coordinator init: Host={self.host}, Port={self.port}, Slave ID={self.slave_id}")

        # Überprüfe, ob Host und Port korrekt sind
        if not self.host or not self.port:
            # _LOGGER.error(f"Host oder Port ist None: Host={self.host}, Port={self.port}")
            raise ValueError("Ungültiger Host oder Port für den Modbus-Client.")

        super().__init__(
            hass,
            _LOGGER,
            name="LambdaHeatpumpCoordinator",
            update_interval=timedelta(seconds=10),
        )

    # def add_register(self, register, register_type='int16'):
        # self._registers_to_read.add((register, register_type))
    def add_register(self, register, register_type='int16'):
        self._registers_to_read[register] = register_type
    
    def remove_register(self, register):
        self._registers_to_read.pop(register, None)

    def clear_registers(self):
        self._registers_to_read.clear()

    async def _async_update_data(self):
        try:
            if not self._client or not self._client.is_socket_open():
                self._client = ModbusTcpClient(self.host, self.port)
                if not self._client.connect():
                    raise UpdateFailed(f"Verbindung zum Modbus-Client {self.host}:{self.port} fehlgeschlagen")

            data = {}
            for register, register_type in self._registers_to_read.items():
                result = self._client.read_holding_registers(register, 2 if register_type in ['int32', 'float32'] else 1, unit=self.slave_id)
                if result.isError():
                    _LOGGER.error(f"Fehler beim Lesen von Register {register}: {result}")
                    data[f"register_{register}"] = None
                else:
                    decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big)
                    value = self._decode_value(decoder, register_type)
                    data[f"register_{register}"] = value
                    _LOGGER.debug(f"Register {register} gelesen: {value}")

            return data

        except Exception as err:
            _LOGGER.exception(f"Fehler beim Abrufen der Daten: {err}")
            raise UpdateFailed(f"Fehler beim Abrufen der Daten: {err}")

    def _decode_value(self, decoder, register_type):
        if register_type == 'int16':
            return decoder.decode_16bit_int()
        elif register_type == 'uint16':
            return decoder.decode_16bit_uint()
        elif register_type == 'int32':
            return decoder.decode_32bit_int()
        elif register_type == 'float32':
            return decoder.decode_32bit_float()
        else:
            _LOGGER.error(f"Unbekannter Registertyp {register_type}")
            return None

    async def async_shutdown(self):
        """Schließe die Verbindung beim Herunterfahren."""
        if self._client:
            self._client.close()

    # async def _async_update_data(self):
    #     """Daten von der Wärmepumpe abrufen."""
    #     try:
    #         # _LOGGER.debug("Versuche, Modbus-Client zu erstellen...")

    #         # Erstelle den Modbus-Client
    #         client = ModbusTcpClient(self.host, self.port)
    #         # _LOGGER.debug(f"ModbusTcpClient erstellt mit Host {self.host} und Port {self.port}")
    #         client.connect()
    #         # _LOGGER.debug(f"ModbusTcpClient verbunden mit {self.host}:{self.port}")
    #         if not client.connect():
    #             _LOGGER.error(f"Verbindung zum Modbus-Client {self.host}:{self.port} fehlgeschlagen")
    #             raise UpdateFailed("Verbindung zum Modbus-Client fehlgeschlagen")

    #         data = {}

    #         for register, register_type in self._registers_to_read:
    #             _LOGGER.debug(f"Register-Type: {register_type}...")
    #             result = client.read_holding_registers(register, 2 if register_type == 'int32' else 1, unit=self.slave_id)
    #             if result.isError():
    #                 _LOGGER.error(f"Fehler beim Lesen von Register {register}: {result}")
    #                 data[f"register_{register}"] = None  # Setze None bei Fehler
    #             else:
    #                 decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big)
    #                 if register_type == 'int16':
    #                     value = decoder.decode_16bit_int()
    #                 elif register_type == 'uint16':
    #                     value = decoder.decode_16bit_uint()
    #                 elif register_type == 'int32':
    #                     value = decoder.decode_32bit_int()
    #                 else:
    #                     _LOGGER.error(f"Unbekannter Registertyp {register_type} für Register {register}")
    #                     value = None
    #                 data[f"register_{register}"] = value
    #                 # _LOGGER.debug(f"Register {register} gelesen: {data[f'register_{register}']}")

    #         client.close()
    #         return data

    #     except Exception as err:
    #         _LOGGER.exception(f"Fehler beim Abrufen der Daten: {err}")
    #         raise UpdateFailed(f"Fehler beim Abrufen der Daten: {err}")


        #     # Lese das Register 100 (Beispiel)
        #     result = client.read_holding_registers(100, 1, unit=self.slave_id)
        #     if result.isError():
        #         _LOGGER.error(f"Fehler beim Lesen von Register 100: {result}")
        #         raise UpdateFailed(f"Fehler beim Lesen von Register 100: {result}")
        #     else:
        #         data["register_100"] = result.registers[0]
        #         _LOGGER.debug(f"Register 100 gelesen: {data['register_100']}")

        #     client.close()

        #     return data

        # except Exception as err:
        #     _LOGGER.exception(f"Ausnahme beim Abrufen der Daten: {err}")
        #     raise UpdateFailed(f"Fehler beim Abrufen der Daten: {err}")
