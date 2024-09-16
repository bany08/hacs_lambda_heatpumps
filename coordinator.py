from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.client import ModbusTcpClient
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
        self._registers_to_read = set() 

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

    def add_register(self, register):
        self._registers_to_read.add(register)

    async def _async_update_data(self):
        """Daten von der Wärmepumpe abrufen."""
        try:
            # _LOGGER.debug("Versuche, Modbus-Client zu erstellen...")

            # Erstelle den Modbus-Client
            client = ModbusTcpClient(self.host, self.port)
            # _LOGGER.debug(f"ModbusTcpClient erstellt mit Host {self.host} und Port {self.port}")
            client.connect()
            # _LOGGER.debug(f"ModbusTcpClient verbunden mit {self.host}:{self.port}")
            if not client.connect():
                _LOGGER.error(f"Verbindung zum Modbus-Client {self.host}:{self.port} fehlgeschlagen")
                raise UpdateFailed("Verbindung zum Modbus-Client fehlgeschlagen")

            data = {}

            for register in self._registers_to_read:
                result = client.read_holding_registers(register, 1, unit=self.slave_id)
                if result.isError():
                    _LOGGER.error(f"Fehler beim Lesen von Register {register}: {result}")
                    data[f"register_{register}"] = None  # Setze None bei Fehler
                else:
                    data[f"register_{register}"] = result.registers[0]
                    # _LOGGER.debug(f"Register {register} gelesen: {data[f'register_{register}']}")

            client.close()
            return data

        except Exception as err:
            _LOGGER.exception(f"Fehler beim Abrufen der Daten: {err}")
            raise UpdateFailed(f"Fehler beim Abrufen der Daten: {err}")


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
