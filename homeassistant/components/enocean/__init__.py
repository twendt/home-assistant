"""
EnOcean Component.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/EnOcean/
"""
import logging

import voluptuous as vol

from homeassistant.const import CONF_DEVICE
import homeassistant.helpers.config_validation as cv
from enocean.protocol.constants import PACKET, RETURN_CODE
from enocean.protocol.packet import RadioPacket
from enocean.utils import to_hex_string

REQUIREMENTS = ['enocean==0.40']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'enocean'

ENOCEAN_DONGLE = None

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_DEVICE): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)

SERVICE_TEACH_IN = 'teach_in'
SERVICE_DESCRIPTIONS = {
    "teach_in": {
        "description": "Send teachin telegram to device",
        "fields": {
            "entity_id": {
                "description": "The entity id of the device to send the teachin to",
                "example": "light.my_dimmer",
            },
        },
    },
}

def setup(hass, config):
    """Set up the EnOcean component."""
    global ENOCEAN_DONGLE

    def handle_teach_in(call):
        """Send teach in telegram."""
        entity_id = call.data.get("entity_id")
        if entity_id is None:
            return
        for device in ENOCEAN_DONGLE.devices:
            if entity_id == device.entity_id:
                try:
                    device.teach_in()
                except:
                    _LOGGER.error("Failed to call teachin for device: %s", entity_id)


    serial_dev = config[DOMAIN].get(CONF_DEVICE)

    ENOCEAN_DONGLE = EnOceanDongle(hass, serial_dev)

    hass.services.register(DOMAIN, SERVICE_TEACH_IN, handle_teach_in,
                      description=SERVICE_DESCRIPTIONS.get(SERVICE_TEACH_IN))

    return True


class EnOceanDongle:
    """Representation of an EnOcean dongle."""

    def __init__(self, hass, ser):
        """Initialize the EnOcean dongle."""
        self.hass = hass
        from enocean.communicators.serialcommunicator import SerialCommunicator
        self.__communicator = SerialCommunicator(
            port=ser, callback=self.callback)
        self.__communicator.start()
        self.get_baseid()
        self.devices = []

    def get_baseid(self):
        """Send command to read  base id to adapter.

        The response will be parsed by the callback function
        """
        return self.__communicator.base_id

    def register_device(self, dev):
        """Register another device."""
        self.devices.append(dev)

    def send_command(self, command):
        """Send a command from the EnOcean dongle."""
        self.__communicator.send(command)

    def callback(self, packet):
        """Handle EnOcean device's callback.

        This is the callback function called by python-enocan whenever there
        is an incoming packet.
        """
        if isinstance(packet, RadioPacket):
            #These packets are the ack packets from switches/lights and rocker switches
            sender_id_hex = to_hex_string(packet.sender)
            _LOGGER.info("Got packet from %s", sender_id_hex)
            for device in self.devices:
                if sender_id_hex == device.dev_id:
                    device.process_telegram(packet)
        else:
            #This is the response packet of the get baseid command
            if packet.packet_type == PACKET.RESPONSE and \
               packet.response == RETURN_CODE.OK and \
               len(packet.response_data) == 4:
                baseid = to_hex_string(packet.response_data)
                _LOGGER.info("Baseid: %s", baseid)
                attrs = {"baseid": baseid}
                self.hass.states.set(
                    "{}.{}".format(DOMAIN, baseid.replace(":", "").
                                   lower()), "Ready", attributes=attrs)


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

