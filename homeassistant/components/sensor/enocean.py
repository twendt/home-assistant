"""
Support for EnOcean sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.enocean/
"""
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_ID)
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components import enocean

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'EnOcean sensor'
DEPENDENCIES = ['enocean']

CONF_EEP = 'eep'
CONF_STATE_SHORTCUT = 'state_shortcut'
CONF_STATE_ATTRIBUTES = 'state_attributes'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ID): cv.string,
    vol.Required(CONF_EEP): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_STATE_SHORTCUT): cv.string,
    vol.Optional(CONF_STATE_ATTRIBUTES): cv.string,
})

def _get_eep_to_class_map():
    eep_to_class_map = {
        'F6:10:00': EnOceanSensorF61000,
        'F6:02:02': EnOceanSensorF60202,
    }
    return eep_to_class_map

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up an EnOcean sensor device."""
    dev_id = config.get(CONF_ID)
    eep = config.get(CONF_EEP)
    devname = config.get(CONF_NAME)
    state_shortcut = config.get(CONF_STATE_SHORTCUT)
    state_attributes = config.get(CONF_STATE_ATTRIBUTES)

    eep_to_class_map = _get_eep_to_class_map()

    if eep in eep_to_class_map:
        #add_devices([eep_to_class_map[eep](dev_id, devname, eep, state_shortcut, state_attributes)])
        add_devices([EnOceanSensor(dev_id, devname, eep, state_shortcut, state_attributes)])


class EnOceanSensor(enocean.EnOceanDevice, Entity):
    """Representation of an EnOcean sensor device"""

    def __init__(self, dev_id, devname, eep, state_shortcut, state_attributes):
        """Initialize the EnOcean sensor device."""
        enocean.EnOceanDevice.__init__(self)
        self.mystate = None
        self.dev_id = dev_id
        self.devname = devname
        self.eep = eep
        self.rorg, self.func, self.type = self._get_eep_hex_values(eep)
        self._parsed = {}
        self._state_shortcut = state_shortcut
        self._state_attributes = state_attributes

    def _get_eep_hex_values(self, eep):
        rorg_str, func_str, type_str = eep.split(':')
        return self._get_int_from_str(rorg_str), self._get_int_from_str(func_str), self._get_int_from_str(type_str)

    def _get_int_from_str(self, str):
        hex_int = int("0x{}".format(str), 16)
        return hex_int

    @property
    def name(self):
        """Return the name of the device."""
        return '%s' % self.devname

    def process_telegram(self, packet):
        """Process incming telegram."""
        packet.parse_eep(self.func, self.type)
        self._parsed = packet.parsed
        if self._state_shortcut in self._parsed:
            self.mystate =  self._parsed[self._state_shortcut]['raw_value']
        else:
            self.mystate = None
        self.schedule_update_ha_state()
        return

    def _get_state(packet):
        """EEP specific funtion to get state."""
        if self._state_shortcut in self._parsed:
            return self._parsed[self._state_shortcut]['raw_value']
        else:
            return None

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
    def _get_state(self, packet, parsed):
        """Return the name of the device."""
        return parsed['WIN']['value']

class EnOceanSensorF60202(EnOceanSensor):
    """Representation of an EnOcean sensor device using EEP F6:02:02"""
    def _get_state(self, packet, parsed):
        """Return the name of the device."""
        eb = parsed['EB']['raw_value']
        sa = parsed['SA']['raw_value']
        r1 = parsed['R1']['raw_value']
        r2 = parsed['R2']['raw_value']
        values = {
            -1: 'off',
            0: 'AI',
            1: 'AO',
            2: 'BI',
            3: 'BO'}

        if eb == 1:
            if sa == 0:
                mystate = values[r1]
            else:
                mystate = "{}{}".format(values[r1], values[r2])
        else:
            mystate = values[-1]
        return mystate
