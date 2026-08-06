from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    # Setup logic assuming you have a coordinator managing the devices
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    # Loop through your devices/pools (adapt to your existing data structure)
    for mac, device_data in coordinator.data.items():
        entities.append(WaterGuruOverrideSwitch(coordinator, mac))
        
    async_add_entities(entities)

class WaterGuruOverrideSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False
    
    def __init__(self, coordinator, mac):
        self.coordinator = coordinator
        self.mac = mac
        self._attr_unique_id = f"{mac}_cassette_override"
        self._attr_name = "Temporarily Allow Early Cassette Replacement"
        self._attr_is_on = False

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.mac)}}

    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        self.async_write_ha_state()
