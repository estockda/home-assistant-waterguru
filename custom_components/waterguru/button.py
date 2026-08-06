from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import STATE_ON
from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    # Loop through your devices/pools (adapt to your existing data structure)
    for mac, device_data in coordinator.data.items():
        entities.append(WaterGuruResetButton(hass, coordinator, mac))
        
    async_add_entities(entities)


class WaterGuruResetButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    
    def __init__(self, hass, coordinator, mac):
        self.hass = hass
        self.coordinator = coordinator
        self.mac = mac
        self._attr_unique_id = f"{mac}_replace_cassette"
        self._attr_name = "Replace Cassette"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self.mac)}}

    async def async_press(self):
        # 1. Get current days remaining from your coordinator data
        device_data = self.coordinator.data.get(self.mac, {})
        days_remaining = device_data.get("cassette_days_remaining", 0)

        # 2. Check the state of the override switch
        override_switch_id = f"switch.waterguru_{self.mac.lower()}_temporarily_allow_early_cassette_replacement"
        override_state = self.hass.states.get(override_switch_id)
        
        is_overridden = override_state is not None and override_state.state == STATE_ON

        # 3. Validation Logic
        if days_remaining > 0 and not is_overridden:
            raise HomeAssistantError(
                f"Cannot replace: {days_remaining} days remaining. "
                "Enable the 'Temporarily Allow Early Cassette Replacement' switch to bypass."
            )

        # 4. Execute the mock API call
        api = self.hass.data[DOMAIN]["api"]
        await self.hass.async_add_executor_job(api.reset_cassette, self.mac)

        # 5. Refresh coordinator to fetch the updated 32-day value immediately
        await self.coordinator.async_request_refresh()

        # 6. Auto-reset the override switch to Off
        if is_overridden:
            await self.hass.services.async_call(
                "switch",
                "turn_off",
                {"entity_id": override_switch_id},
                blocking=False
            )
