"""
EnOcean Component.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/EnOcean/
"""
import logging

import voluptuous as vol

from homeassistant.const import CONF_DEVICE
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['https://github.com/kipe/enocean'
                '/archive/7a0b619471d3ad9b71d897a8f2ffa3cd8ab8f9f3.zip'
                '#enocean==0.39']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'enocean'

ENOCEAN_DONGLE = None

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_DEVICE): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the EnOcean component."""
    global ENOCEAN_DONGLE

    serial_dev = config[DOMAIN].get(CONF_DEVICE)

    ENOCEAN_DONGLE = EnOceanDongle(hass, serial_dev)

    return True


class EnOceanDongle:
    """Representation of an EnOcean dongle."""

    def __init__(self, hass, ser):
        """Initialize the EnOcean dongle."""
        from enocean.communicators.serialcommunicator import SerialCommunicator
        self.__communicator = SerialCommunicator(
            port=ser, callback=self.callback)
        self.__communicator.start()
        self.__devices = []

    def register_device(self, dev):
        """Register another device."""
        self.__devices.append(dev)

    def send_command(self, command):
        """Send a command from the EnOcean dongle."""
        self.__communicator.send(command)

    def callback(self, temp):
        """Handle EnOcean device's callback.

        This is the callback function called by python-enocan whenever there
        is an incoming packet.
        """
        from enocean.protocol.packet import RadioPacket
        from enocean.utils import to_hex_string
        if isinstance(temp, RadioPacket):
            for device in self.__devices:
                if to_hex_string(temp.sender) == device.dev_id:
                    device.process_telegram(temp)


class EnOceanDevice():
    """Parent class for all devices associated with the EnOcean component."""

    def __init__(self):
        """Initialize the device."""
        ENOCEAN_DONGLE.register_device(self)
        self.stype = ""
        self.sensorid = [0x00, 0x00, 0x00, 0x00]

    # pylint: disable=no-self-use
    def send_command(self, packet):
        """Send a command via the EnOcean dongle."""
        ENOCEAN_DONGLE.send_command(packet)
