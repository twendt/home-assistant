"""
Support for EnOcean switches.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.enocean/
"""
import logging

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_ID)
from homeassistant.components import enocean
from homeassistant.components.enocean.const import  CONF_SENDER_ID, CONF_EEP
from homeassistant.components.enocean.commands import (
    gateway_switch_on, gateway_switch_off)
from homeassistant.components.enocean.states import rps_r1_binary_ack_state
from homeassistant.components.enocean.teach import generate_eltako_38_teachin
from homeassistant.components.enocean.util import get_hex_list_from_str
from homeassistant.helpers.entity import ToggleEntity
import homeassistant.helpers.config_validation as cv
from enocean.protocol.packet import RadioPacket
from enocean.protocol.constants import RORG

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'EnOcean Switch'
DEPENDENCIES = ['enocean']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ID): cv.string,
    vol.Required(CONF_SENDER_ID): cv.string,
    vol.Required(CONF_EEP): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the EnOcean switch platform."""
    sender_id = config.get(CONF_SENDER_ID)
    devname = config.get(CONF_NAME)
    dev_id = config.get(CONF_ID)
    eep = config.get(CONF_EEP)
    eep_class = globals()["EnOceanSwitch{}".format(eep.replace(":", ""))]
    try:
        add_devices([eep_class(sender_id, devname, dev_id, eep)])
    except NameError:
        _LOGGER.error("Failed to load class for eep %s", eep)

class EnOceanSwitch(enocean.EnOceanDevice, ToggleEntity):
    """Representation of an EnOcean switch device."""

    def __init__(self, sender_id, devname, dev_id, eep):
        """Initialize the EnOcean switch device."""
        enocean.EnOceanDevice.__init__(self)
        self.dev_id = dev_id
        self._devname = devname
        self._on_state = False
        self._sender_id = sender_id
        self._eep = eep
        self._rorg, self._func, self._type = get_hex_list_from_str(eep)

    @property
    def is_on(self):
        """Return whether the switch is on or off."""
        return self._on_state

    @property
    def name(self):
        """Return the device name."""
        return self._devname

#    def turn_on(self, **kwargs):
#        """Turn on the switch."""
#        optional = [0x03, ]
#        optional.extend(self.dev_id)
#        optional.extend([0xff, 0x00])
#        self.send_command(data=[0xD2, 0x01, 0x00, 0x64, 0x00,
#                                0x00, 0x00, 0x00, 0x00], optional=optional,
#                          packet_type=0x01)
#        self._on_state = True
#
#    def turn_off(self, **kwargs):
#        """Turn off the switch."""
#        optional = [0x03, ]
#        optional.extend(self.dev_id)
#        optional.extend([0xff, 0x00])
#        self.send_command(data=[0xD2, 0x01, 0x00, 0x00, 0x00,
#                                0x00, 0x00, 0x00, 0x00], optional=optional,
#                          packet_type=0x01)
#        self._on_state = False
#
#    def value_changed(self, val):
#        """Update the internal state of the switch."""
#        self._on_state = val
#        self.schedule_update_ha_state()

class EnOceanSwitchA53808(EnOceanSwitch):
    """Representation of an EnOcean switch using EEP ."""

    def send_switch_command(self, new_state):
        """Send switch command to adapter."""
        _LOGGER.info("Sending switch command")
        new_state_int = 1 if new_state else 0
        try:
            pack = RadioPacket.create(
                rorg=RORG.BS4,
                rorg_func=self._func,
                rorg_type=self._type,
                sender=get_hex_list_from_str(self._sender_id),
                destination=get_hex_list_from_str(self.dev_id),
                command=1,
                TIM=0,
                LRNB=1,
                LCK=0,
                DEL=0,
                SW=new_state_int)
            self.send_command(pack)
        except:
            _LOGGER.error("Failed to send EnOcean packet")

    def send_packet(self, pack):
        """Send packet to adapter."""
        if pack:
            try:
                self.send_command(pack)
            except:
                _LOGGER.error("Failed to send EnOcean packet")

    def turn_on(self, **kwargs):
        """Turn the switch source on"""
        pack = gateway_switch_on(self._sender_id, self.dev_id)
        self.send_packet(pack)

    def turn_off(self, **kwargs):
        """Turn the switch source off."""
        pack = gateway_switch_off(self._sender_id, self.dev_id)
        self.send_packet(pack)

    def teach_in(self, **kwargs):
        """Send learn telegram to the device"""
        pack = generate_eltako_38_teachin(self._sender_id, self.dev_id)
        try:
            self.send_command(pack)
        except:
            _LOGGER.error("Failed to send EnOcean packet")

    def process_telegram(self, packet):
        """Process incming telegram."""
        if packet.rorg != RORG.RPS:
            return
        self._on_state = rps_r1_binary_ack_state(packet)
        self.schedule_update_ha_state()
#        try:
#            packet.parse_eep(2, 2)
#            parsed = packet.parsed
#            self._get_state(packet, parsed)
#            self.schedule_update_ha_state()
#        except:
#            _LOGGER.error("Failed to parse ack packet")
        return

#    def _get_state(self, packet, parsed):
#        """EEP specific funtion to get state."""
#        r1_val = parsed['R1']['raw_value']
#
#        if r1_val == 3:
#            self._on_state = True
#        if r1_val == 2:
#            self._on_state = False
#        return
