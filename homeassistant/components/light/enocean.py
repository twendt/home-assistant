"""
Support for EnOcean light sources.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.enocean/
"""
import logging
import math

import voluptuous as vol

from homeassistant.components.light import (
    Light, ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, CONF_ID)
from homeassistant.components import enocean
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_SENDER_ID = 'sender_id'
CONF_EEP = 'eep'

DEFAULT_NAME = 'EnOcean Light'
DEPENDENCIES = ['enocean']

SUPPORT_ENOCEAN = SUPPORT_BRIGHTNESS

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ID): cv.string,
    vol.Required(CONF_SENDER_ID): cv.string,
    vol.Required(CONF_EEP): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the EnOcean light platform."""
    sender_id = config.get(CONF_SENDER_ID)
    devname = config.get(CONF_NAME)
    dev_id = config.get(CONF_ID)
    eep = config.get(CONF_EEP)

    add_devices([EnOceanLight(sender_id, devname, dev_id, eep)])


class EnOceanLight(enocean.EnOceanDevice, Light):
    """Representation of an EnOcean light source."""

    def __init__(self, sender_id, devname, dev_id, eep):
        """Initialize the EnOcean light source."""
        enocean.EnOceanDevice.__init__(self)
        self._on_state = False
        self._brightness = 50
        self._sender_id = sender_id
        self.dev_id = dev_id
        self._devname = devname
        self._eep = eep
        self._rorg, self._func, self._type = self._get_hex_list_from_str(eep)

    def _get_hex_list_from_str(self, str):
        #rorg_str, func_str, type_str = eep.split(':')
        #return self._get_int_from_str(rorg_str), self._get_int_from_str(func_str), self._get_int_from_str(type_str)
        return [ self._get_int_from_str(part_str) for part_str in str.split(':') ]

    def _get_int_from_str(self, str):
        hex_int = int("0x{}".format(str), 16)
        return hex_int

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._devname

    @property
    def brightness(self):
        """Brightness of the light.

        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self):
        """If light is on."""
        return self._on_state

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_ENOCEAN

    def turn_on(self, **kwargs):
        """Turn the light source on or sets a specific dimmer value."""
        from enocean.protocol.packet import RadioPacket
        from enocean.protocol.constants import RORG
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None:
            self._brightness = brightness
        else:
            self._brightness = 256

        bval = math.floor(self._brightness / 256.0 * 100.0)
        if bval == 0:
            sw = 0
        else:
            sw = 1
        pack = RadioPacket.create(rorg=RORG.BS4, rorg_func=self._func, rorg_type=self._type,
                              sender=self._get_hex_list_from_str(self._sender_id),
                              destination=self._get_hex_list_from_str(self.dev_id),
                              command=2,
                              EDIM=bval,
                              RMP=1,
                              LRNB=1,
                              EDIMR=0,
                              STR=0,
                              SW=sw)
        self.send_command(pack)
        self._on_state = True

    def turn_off(self, **kwargs):
        """Turn the light source off."""
        from enocean.protocol.packet import RadioPacket
        from enocean.protocol.constants import RORG
        pack = RadioPacket.create(rorg=RORG.BS4, rorg_func=self._func, rorg_type=self._type,
                              sender=self._get_hex_list_from_str(self._sender_id),
                              destination=self._get_hex_list_from_str(self.dev_id),
                              command=2,
                              EDIM=1,
                              RMP=1,
                              LRNB=1,
                              EDIMR=0,
                              STR=0,
                              SW=0)
        self.send_command(pack)
        self._on_state = False

    def process_telegram(self, packet):
        """Process incming telegram."""
        from enocean.protocol.constants import RORG
        if packet.rorg != RORG.BS4:
            return
        _LOGGER.info("Running process telegram")
        _LOGGER.info("Func: {}, Type: {}".format(self._func, self._type))
        packet.parse_eep(self._func, self._type, command=2)
        parsed = packet.parsed
        self.mystate = self._get_state(packet, parsed)
        _LOGGER.info("On State: {}".format(self._on_state))
        _LOGGER.info("Brightness: {}".format(self._brightness))
        self.schedule_update_ha_state()
        return

    def _get_state(self, packet, parsed):
        """EEP specific funtion to get state."""
        edim = parsed['EDIM']['raw_value']
        sw = parsed['SW']['raw_value']

        if sw == 1:
            self._brightness = math.floor(edim / 100.0 * 256.0)
            self._on_state = True
        else:
            self._on_state = False
            self._brightness = 0
        return
