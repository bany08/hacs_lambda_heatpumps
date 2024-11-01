"""Climate platform for Lambda Heatpumps."""
from __future__ import annotations

import logging
from typing import Any
from dataclasses import dataclass
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    HVACMode,
    HVACAction,
    ClimateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER
from .coordinator import LambdaHeatpumpCoordinator


_LOGGER = logging.getLogger(__name__)

@dataclass
class LambdaClimateEntityDescription(ClimateEntityDescription):
    register_temp: int = 0
    register_setpoint: int = 0
    register_setpoint_high: int = 30
    register_setpoint_low: int = 70
    register_mode: int = 0
    factor: float = 1.0
    data_type: str = "int16"

CLIMATE_DESCRIPTIONS: tuple[LambdaClimateEntityDescription, ...] = (
    LambdaClimateEntityDescription(
        key="boiler_1_climate",
        name="Boiler 1 Climate",
        register_temp=2002,  # Angenommenes Register für aktuelle Temperatur
        register_setpoint=2050,  # Register für Solltemperatur (Maximum Boiler Temperature)
        register_mode=2001,  # Angenommenes Register für Betriebsmodus
        factor=0.1,
        register_setpoint_high = 30,
        register_setpoint_low = 70, 
        data_type="int16",
    ),
    # Fügen Sie hier weitere ClimateEntityDescriptions hinzu
)

class LambdaHeatpumpClimate(ClimateEntity):
    """Representation of a Lambda Heatpump climate device."""

    def __init__(
        self,
        coordinator: LambdaHeatpumpCoordinator,
        config_entry: ConfigEntry,
        description: LambdaClimateEntityDescription,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the climate device."""
        self.coordinator = coordinator
        self.entity_description = description
        self._config_entry = config_entry

        self._attr_name = description.name
        self._attr_unique_id = f"{config_entry.entry_id}_{description.key}"
        self._attr_device_info = device_info

        
        self._attr_hvac_modes = [HVACMode.HEAT]
        self._attr_hvac_mode = HVACMode.HEAT

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._target_temp_high = None
        self._target_temp_low = None

        self.coordinator.add_register(description.register_temp, "int16")
        self.coordinator.add_register(description.register_setpoint, "int16")
        self.coordinator.add_register(description.register_mode, "int16")


        _LOGGER.debug("Description: %s", description)
        _LOGGER.debug("Übersetzung: %s", self.entity_description.key)

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        value = self.coordinator.data.get(f"register_{self.entity_description.register_temp}")
        if value is None:
            return None
        return value * self.entity_description.factor

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        value = self.coordinator.data.get(f"register_{self.entity_description.register_setpoint}")
        if value is None:
            return None
        return value * self.entity_description.factor

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode."""
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation."""
        current_temp = self.current_temperature
        target_temp = self.target_temperature
    
        if current_temp is None or target_temp is None:
            return None

        if current_temp < target_temp:
            return HVACAction.HEATING
        return HVACAction.IDLE
    
    @property
    def target_temperature_step(self) -> float:
        return 0.5
    
    @property
    def target_temperature_high(self) -> float | None:
        return self._target_temp_high
    
    @property
    def target_temperature_low(self) -> float | None:
        return self._target_temp_low

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        scaled_temp = int(temperature / self.entity_description.factor)
        await self.coordinator.async_write_register(
            self.entity_description.register_setpoint, 
            scaled_temp,
            register_type='int16'  # oder der entsprechende Typ für Ihr Register
        )
        await self.coordinator.async_request_refresh()
    
    
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.HEAT:
            await self.coordinator.async_write_register(self.entity_description.register_mode, 1)
        elif hvac_mode == HVACMode.OFF:
            await self.coordinator.async_write_register(self.entity_description.register_mode, 0)
        await self.coordinator.async_request_refresh()

    async def _async_set_target_temp(self, temperature):
        """Set new target temperature."""
        await self.coordinator.async_write_register(
            self.entity_description.register_setpoint, 
            int(temperature / self.entity_description.factor), 
            register_type='int16'
        )

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 25  # Beispielwert, passen Sie dies an Ihre Anforderungen an

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 70  # Beispielwert, passen Sie dies an Ihre Anforderungen an

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    num_boilers = config_entry.data.get("amount_of_boilers", 1)
    model = config_entry.data.get("model", "Unknown Model")

    device_infos = {}
    for i in range(1, num_boilers + 1):
        device_infos[f"boiler_{i}"] = DeviceInfo(
            identifiers={(DOMAIN, f"{config_entry.entry_id}_boiler_{i}")},
            name=f"Lambda Boiler {i}",
            manufacturer=MANUFACTURER,
            model=model,
        )

    climate_devices = []
    for description in CLIMATE_DESCRIPTIONS:
        if "boiler_" in description.key and int(description.key.split('_')[1]) > num_boilers:
            continue

        category = description.key.split('_')[0]
        device_info = device_infos.get(f"{category}_{description.key.split('_')[1]}", None)

        if device_info:
            climate_device = LambdaHeatpumpClimate(
                coordinator=coordinator,
                config_entry=config_entry,
                description=description,
                device_info=device_info, 
            )
            climate_devices.append(climate_device)

    async_add_entities(climate_devices)