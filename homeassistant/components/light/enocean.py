"""
Support for EnOcean light sources.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.enocean/
"""
import logging

import voluptuous as vol

from homeassistant.components.light import (
    Light, ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, CONF_ID)
from homeassistant.components import enocean
from homeassistant.components.enocean.const import  CONF_SENDER_ID, CONF_EEP
from homeassistant.components.enocean.commands import (
    gateway_dim_on, gateway_dim_off)
from homeassistant.components.enocean.states import gateway_dim_state
from homeassistant.components.enocean.teach import generate_eltako_38_teachin
from homeassistant.components.enocean.util import get_hex_list_from_str
import homeassistant.helpers.config_validation as cv
from enocean.protocol.constants import RORG

_LOGGER = logging.getLogger(__name__)

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
    eep_class = globals()["EnOceanLight{}".format(eep.replace(":", ""))]
    try:
        add_devices([eep_class(sender_id, devname, dev_id, eep)])
    except NameError:
        _LOGGER.error("Failed to load class for eep %s", eep)

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
        self._rorg, self._func, self._type = get_hex_list_from_str(eep)

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

class EnOceanLightA53808(EnOceanLight):
    """Representation of an EnOcean light using EEP ."""

    def turn_on(self, **kwargs):
        """Turn the light source on or sets a specific dimmer value."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None:
            self._brightness = brightness
        else:
            self._brightness = 256

        pack = gateway_dim_on(self._sender_id, self.dev_id, self._brightness)
        if pack:
            self.send_command(pack)

    def turn_off(self, **kwargs):
        """Turn the light source off."""
        pack = gateway_dim_off(self._sender_id, self.dev_id)
        if pack:
            self.send_command(pack)

    def teach_in(self, **kwargs):
        """Send learn telegram to the device"""
        pack = generate_eltako_38_teachin(self._sender_id, self.dev_id)
        try:
            self.send_command(pack)
        except:
            _LOGGER.error("Failed to send EnOcean packet")


    def process_telegram(self, packet):
        """Process incming telegram."""
        if packet.rorg != RORG.BS4:
            return
        try:
            self._on_state, self._brightness = gateway_dim_state(packet)
            self.schedule_update_ha_state()
        except:
            _LOGGER.error("Failed to parse packet")
        return
