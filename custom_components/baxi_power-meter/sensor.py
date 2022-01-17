import logging

from .helper import convert_datetime_to_timestamp, create_sensor_name
from homeassistant.helpers.reload import async_setup_reload_service
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import datetime
from datetime import timedelta
from typing import Callable, List, Optional
from .const import *
from homeassistant.const import (
    CONF_NAME,
)
from homeassistant.core import callback

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from .config_schema import CONF_PERIOD1, CONF_PERIOD2, CONF_PERIOD3

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=10)


async def async_create_entities(hass, config_entry, async_add_devices):
    period1 = config_entry.data.get(CONF_PERIOD1, None)
    if not period1:
        # Working in single period mode, just one sensor
        await async_setup_reload_service(hass, DOMAIN, PLATFORM)
        async_add_devices(
            [
                BaxiEnergyConsumptionSensor(hass, config_entry.data),
            ],
            update_before_add=True,
        )
    else:
        # Working in 3 period mode
        period2 = config_entry.data.get(CONF_PERIOD2, None)
        period3 = config_entry.data.get(CONF_PERIOD3, None)

        period_lookup_table = PeriodLookupTable()
        period_lookup_table.add_period(CONF_PERIOD1, period1)
        period_lookup_table.add_period(CONF_PERIOD2, period2)
        period_lookup_table.add_period(CONF_PERIOD3, period3)

        await async_setup_reload_service(hass, DOMAIN, PLATFORM)
        async_add_devices(
            [
                BaxiEnergyConsumptionSensor(hass, CONF_PERIOD1, period_lookup_table),
                BaxiEnergyConsumptionSensor(hass, CONF_PERIOD2, period_lookup_table),
                BaxiEnergyConsumptionSensor(hass, CONF_PERIOD3, period_lookup_table),
            ],
            update_before_add=True,
        )


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:

    config = hass.data[PLATFORM].get(DATA_KEY_CONFIG)

    """Add BaxiEnergyConsumptionSensor entities from configuration.yaml."""
    _LOGGER.warning(
        "Setup entity coming from configuration.yaml named: %s. Device will not be created, only entities",
        config.get(CONF_NAME),
    )
    await async_create_entities(hass, config, async_add_entities)


async def async_setup_entry(hass, config_entry, async_add_devices):
    await async_create_entities(hass, config_entry, async_add_devices)


class BaxiEnergyConsumptionSensor(SensorEntity, RestoreEntity):
    """BaxiEnergyConsumptionSensor"""

    def __init__(self, hass, period_name, period_lookup_table):
        """Initialize the sensor."""
        super().__init__()
        self.hass = hass
        self._baxi_api = hass.data[PLATFORM].get(DATA_KEY_API)
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_should_poll = True
        self._period_name = period_name
        self._attr_name = create_sensor_name(
            self._baxi_api.get_device_information().get(NAME_KEY), period_name
        )
        self._attr_unique_id = self._attr_name
        self.period_lookup_table = period_lookup_table
        self._attr_native_unit_of_measurement = "kWh"
        self._attr_extra_state_attributes = {}
        self._last_sample_time = 0
        self._attr_device_info = {
            "identifiers": {
                (
                    SERIAL_ID_KEY,
                    self._baxi_api.get_device_information().get(DEVICE_ID_KEY, "1234"),
                )
            }
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._baxi_api.is_bootstraped()

    async def async_update(self):

        if self.period_lookup_table and not self.period_lookup_table.is_current_period(
                self._period_name
        ):
            return

        now = datetime.datetime.now()
        timestamp_now = convert_datetime_to_timestamp(now)
        timestamp_one_hour_ago = convert_datetime_to_timestamp(
            now - datetime.timedelta(hours=1)
        )
        samples = await self._baxi_api.get_samples_between_dates(
            timestamp_one_hour_ago, timestamp_now
        )
        if not samples or len(samples) < 2:
            return
        last_sample = samples[-1]
        current_sample_time = last_sample["t"]
        if current_sample_time == self._last_sample_time:
            # If samples in Baxi has not been updated, we don't do it neither
            return
        self._last_sample_time = current_sample_time

        second_last_sample = samples[-2]
        period_increment = (float(last_sample["counter"]) - float(second_last_sample["counter"])) / 1000  # in kWh

        if self._attr_native_value:
            self._attr_native_value = self._attr_native_value + period_increment
        else:
            self._attr_native_value = period_increment


        self._attr_extra_state_attributes[
            LAST_KNOWN_STATE_KEY
        ] = self._attr_native_value
        self._attr_extra_state_attributes[LAST_SAMPLE_TIME_KEY] = current_sample_time

    async def async_added_to_hass(self):
        """Call when the sensor is added to hass."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._attr_native_value = state.attributes.get(LAST_KNOWN_STATE_KEY, None)
            self._last_sample_time = state.attributes.get(LAST_SAMPLE_TIME_KEY, None)
        self.async_write_ha_state()


class PeriodLookupTable:
    def __init__(self) -> None:
        self._lookup_table = list()

    def add_period(self, period_name, config):
        if len(self._lookup_table) == 0:
            self._lookup_table = [None] * 168  # One week has 168 hours

        for period in config.split(";"):
            if period.lower() == "weekend":
                # special handling for weekend
                for day in [5, 6]:
                    for hour in range(0, 24):
                        position = day * 24 + hour
                        self._lookup_table[position] = period_name
            else:
                start, end = period.split("-", 1)
                start = int(start)
                end = int(end)
                for day in range(0, 5):
                    for hour in range(start, end):
                        position = day * 24 + hour
                        self._lookup_table[position] = period_name

    def is_current_period(self, period_name):
        now = datetime.datetime.now()
        weekday = now.weekday()
        hour = now.hour

        position = weekday * 24 + hour
        return self._lookup_table[position] == period_name
