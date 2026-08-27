from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers import entity_registry as er
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import STATE_ON
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for device in coordinator.data.values():
        entities.append(WaterGuruResetButton(hass, coordinator, device))
        entities.append(WaterGuruMeasureButton(hass, coordinator, device))

    async_add_entities(entities)

class WaterGuruResetButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    
    def __init__(self, hass, coordinator, device):
        self.hass = hass
        self.coordinator = coordinator
        self.device = device
        self._attr_unique_id = f"{device.device_id}_replace_cassette"
        self._attr_translation_key = "replace_cassette"

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, self.device.device_id)})

    async def async_press(self):
        device_data = self.coordinator.data.get(self.device.device_id)
        if not device_data:
            raise HomeAssistantError("Device data not available.")
            
        pct_remaining = device_data.sensors.get("cassette", 0)
        days_remaining = device_data.sensors.get("cassette_days_remaining")

        registry = er.async_get(self.hass)
        switch_unique_id = f"{self.device.device_id}_cassette_override"
        override_switch_id = registry.async_get_entity_id("switch", DOMAIN, switch_unique_id)
        
        override_state = self.hass.states.get(override_switch_id) if override_switch_id else None
        is_overridden = override_state is not None and override_state.state == STATE_ON

        if pct_remaining > 0 and not is_overridden:
            if days_remaining is not None:
                error_msg = f"Cannot replace: {days_remaining} days remaining."
            else:
                error_msg = f"Cannot replace: {pct_remaining}% remaining."
                
            error_msg += " Enable the 'Temporarily Allow Early Cassette Replacement' switch to bypass."
            raise HomeAssistantError(error_msg)

        # 1. Turn off the override switch immediately for UI responsiveness
        if is_overridden and override_switch_id:
            await self.hass.services.async_call(
                "switch",
                "turn_off",
                {"entity_id": override_switch_id},
                blocking=False
            )

        # 2. Execute the reset command (incurs network latency)
        api = self.coordinator.api
        await self.hass.async_add_executor_job(api.reset_cassette, device_data.serial_number)

        # 3. Refresh the sensor data (incurs network latency)
        await self.coordinator.async_request_refresh()

class WaterGuruMeasureButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass, coordinator, device):
        self.hass = hass
        self.coordinator = coordinator
        self.device = device
        self._attr_unique_id = f"{device.device_id}_manual_measurement"
        self._attr_translation_key = "manual_measurement"
        self._attr_icon = "mdi:water-sync"

    @property
    def device_info(self):
        return DeviceInfo(identifiers={(DOMAIN, self.device.device_id)})

    async def async_press(self):
        device_data = self.coordinator.data.get(self.device.device_id)
        if not device_data:
            raise HomeAssistantError("Device data not available.")
            
        if not device_data.serial_number:
            raise HomeAssistantError("No podId found for this WaterBody. Cannot trigger measurement.")

        api = self.coordinator.api
        await self.hass.async_add_executor_job(api.measure, device_data.serial_number)
