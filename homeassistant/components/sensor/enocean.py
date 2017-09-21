"""
Support for EnOcean sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.enocean/
"""
import logging

import voluptuous as vol

from homeassistant.components.enocean.const import (
    CONF_EEP, CONF_STATE_SHORTCUT, CONF_STATE_ATTRIBUTES)
from homeassistant.components.enocean.util import get_hex_list_from_str
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_ID)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components import enocean

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'EnOcean sensor'
DEPENDENCIES = ['enocean']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ID): cv.string,
    vol.Required(CONF_EEP): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_STATE_SHORTCUT): cv.string,
    vol.Optional(CONF_STATE_ATTRIBUTES): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up an EnOcean sensor device."""
    dev_id = config.get(CONF_ID)
    eep = config.get(CONF_EEP)
    devname = config.get(CONF_NAME)
    state_shortcut = config.get(CONF_STATE_SHORTCUT)
    state_attributes = config.get(CONF_STATE_ATTRIBUTES)

    eep_class = globals()["EnOceanSensor{}".format(eep.replace(":", ""))]
    try:
        add_devices([eep_class(dev_id, devname, eep, state_shortcut, state_attributes)])
    except NameError:
        _LOGGER.error("Failed to load class for eep %s", eep)

class EnOceanSensor(enocean.EnOceanDevice, Entity):
    """Representation of an EnOcean sensor device"""

    def __init__(self, dev_id, devname, eep, state_shortcut, state_attributes):
        """Initialize the EnOcean sensor device."""
        enocean.EnOceanDevice.__init__(self)
        self.mystate = None
        self.dev_id = dev_id
        self.devname = devname
        self.eep = eep
        self.rorg, self.func, self.type = get_hex_list_from_str(eep)
        self._parsed = {}
        self._state_shortcut = state_shortcut
        self._state_attributes = state_attributes

    @property
    def name(self):
        """Return the name of the device."""
        return '%s' % self.devname

    def process_telegram(self, packet):
        """Process incming telegram."""
        try:
            packet.parse_eep(self.func, self.type)
            self._parsed = packet.parsed
            if self._state_shortcut in self._parsed:
                self.mystate = self._get_state(packet)
            else:
                self.mystate = None
            self.schedule_update_ha_state()
        except:
            pass
        return

    @property
    def state(self):
        """Return the state of the device."""
        return self.mystate

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        attrs = {}
        for k in self._parsed:
            for sub in self._parsed[k]:
                attr_name = "{}_{}".format(k, sub)
                if not self._state_attributes or attr_name in self._state_attributes:
                    attrs[attr_name] = self._parsed[k][sub]
        return attrs

class EnOceanSensorF61000(EnOceanSensor):
    """Representation of an EnOcean sensor device using EEP F6:10:00"""

    ICON_MAP = {
        1: "mdi:arrow-up",
        2: "mdi:arrow-right",
        3: "mdi:arrow-down",
    }


    @property
    def icon(self):
        """Return the icon for the current state"""
        if self.mystate in self.ICON_MAP:
            icon = self.ICON_MAP[self.mystate]
        else:
            icon = "mdi:exclamation"
        return icon

    def _get_state(self, packet):
        """Return the name of the device."""
        return self._parsed['WIN']['raw_value']

class EnOceanSensorF60202(EnOceanSensor):
    """Representation of an EnOcean sensor device using EEP F6:02:02"""

    def __init__(self, dev_id, devname, eep, state_shortcut, state_attributes):
        """Initialize the EnOcean sensor device."""
        EnOceanSensor.__init__(self, dev_id, devname, eep, state_shortcut, state_attributes)
        self.mystate = 'off'

    def _get_state(self, packet):
        """Return the name of the device."""
        eb_val = self._parsed['EB']['raw_value']
        sa_val = self._parsed['SA']['raw_value']
        r1_val = self._parsed['R1']['raw_value']
        r2_val = self._parsed['R2']['raw_value']
        values = {
            -1: 'off',
            0: 'AI',
            1: 'AO',
            2: 'BI',
            3: 'BO'}

        if eb_val == 1:
            if sa_val == 0:
                mystate = values[r1_val]
            else:
                mystate = "{}{}".format(values[r1_val], values[r2_val])
        else:
            mystate = values[-1]
        return mystate
