from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    # Loop over values() to extract the WaterGuruDevice object directly
    for device in coordinator.data.values():
        entities.append(WaterGuruOverrideSwitch(coordinator, device))
        
    async_add_entities(entities)

class WaterGuruOverrideSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    
    def __init__(self, coordinator, device):
        self.coordinator = coordinator
        self.device = device
        self._attr_unique_id = f"{device.device_id}_cassette_override"
        self._attr_translation_key = "cassette_override"
        self._attr_is_on = False

    @property
    def device_info(self):
        # Match sensor.py DeviceInfo linkage exactly
        return DeviceInfo(identifiers={(DOMAIN, self.device.device_id)})

    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        self.async_write_ha_state()
