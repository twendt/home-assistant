"""
Support for the IKEA Tradfri platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.tradfri/
"""
import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, ATTR_RGB_COLOR, SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR_TEMP, SUPPORT_RGB_COLOR, Light)
from homeassistant.components.light import (
    PLATFORM_SCHEMA as LIGHT_PLATFORM_SCHEMA)
from homeassistant.components.tradfri import (
    KEY_GATEWAY, KEY_TRADFRI_GROUPS, KEY_API)
from homeassistant.util import color as color_util

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['tradfri']
PLATFORM_SCHEMA = LIGHT_PLATFORM_SCHEMA
IKEA = 'IKEA of Sweden'
ALLOWED_TEMPERATURES = {IKEA}


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the IKEA Tradfri Light platform."""
    if discovery_info is None:
        return

    gateway_id = discovery_info['gateway']
    api = hass.data[KEY_API][gateway_id]
    gateway = hass.data[KEY_GATEWAY][gateway_id]
    devices = api(gateway.get_devices())
    lights = [dev for dev in devices if api(dev).has_light_control]
    add_devices(Tradfri(light, api) for light in lights)

    allow_tradfri_groups = hass.data[KEY_TRADFRI_GROUPS][gateway_id]
    if allow_tradfri_groups:
        groups = api(gateway.get_groups())
        add_devices(TradfriGroup(group, api) for group in groups)


class TradfriGroup(Light):
    """The platform class required by hass."""

    def __init__(self, light, api):
        """Initialize a Group."""
        self._group = api(light)
        self._api = api
        self._name = self._group.name

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS

    @property
    def name(self):
        """Return the display name of this group."""
        return self._name

    @property
    def is_on(self):
        """Return true if group lights are on."""
        return self._group.state

    @property
    def brightness(self):
        """Return the brightness of the group lights."""
        return self._group.dimmer

    def turn_off(self, **kwargs):
        """Instruct the group lights to turn off."""
        self._api(self._group.set_state(0))

    def turn_on(self, **kwargs):
        """Instruct the group lights to turn on, or dim."""
        if ATTR_BRIGHTNESS in kwargs:
            self._api(self._group.set_dimmer(kwargs[ATTR_BRIGHTNESS]))
        else:
            self._api(self._group.set_state(1))

    def update(self):
        """Fetch new state data for this group."""
        from pytradfri import RequestTimeout
        try:
            self._api(self._group.update())
        except RequestTimeout:
            _LOGGER.warning("Tradfri update request timed out")


class Tradfri(Light):
    """The platform class required by Home Asisstant."""

    def __init__(self, light, api):
        """Initialize a Light."""
        self._light = api(light)
        self._api = api

        # Caching of LightControl and light object
        self._light_control = self._light.light_control
        self._light_data = self._light_control.lights[0]
        self._name = self._light.name
        self._rgb_color = None
        self._features = SUPPORT_BRIGHTNESS

        if self._light_data.hex_color is not None:
            if self._light.device_info.manufacturer == IKEA:
                self._features |= SUPPORT_COLOR_TEMP
            else:
                self._features |= SUPPORT_RGB_COLOR

        self._ok_temps = \
            self._light.device_info.manufacturer in ALLOWED_TEMPERATURES

    @property
    def min_mireds(self):
        """Return the coldest color_temp that this light supports."""
        from pytradfri.color import MAX_KELVIN_WS
        return color_util.color_temperature_kelvin_to_mired(MAX_KELVIN_WS)

    @property
    def max_mireds(self):
        """Return the warmest color_temp that this light supports."""
        from pytradfri.color import MIN_KELVIN_WS
        return color_util.color_temperature_kelvin_to_mired(MIN_KELVIN_WS)

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._features

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._light_data.state

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._light_data.dimmer

    @property
    def color_temp(self):
        """Return the CT color value in mireds."""
        if (self._light_data.kelvin_color is None or
                self.supported_features & SUPPORT_COLOR_TEMP == 0 or
                not self._ok_temps):
            return None
        return color_util.color_temperature_kelvin_to_mired(
            self._light_data.kelvin_color
        )

    @property
    def rgb_color(self):
        """RGB color of the light."""
        return self._rgb_color

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self._api(self._light_control.set_state(False))

    def turn_on(self, **kwargs):
        """
        Instruct the light to turn on.

        After adding "self._light_data.hexcolor is not None"
        for ATTR_RGB_COLOR, this also supports Philips Hue bulbs.
        """
        if ATTR_BRIGHTNESS in kwargs:
            self._api(self._light_control.set_dimmer(kwargs[ATTR_BRIGHTNESS]))
        else:
            self._api(self._light_control.set_state(True))

        if ATTR_RGB_COLOR in kwargs and self._light_data.hex_color is not None:
            self._api(self._light.light_control.set_hex_color(
                color_util.color_rgb_to_hex(*kwargs[ATTR_RGB_COLOR])))

        elif ATTR_COLOR_TEMP in kwargs and \
                self._light_data.hex_color is not None and self._ok_temps:
            kelvin = color_util.color_temperature_mired_to_kelvin(
                kwargs[ATTR_COLOR_TEMP])
            self._api(self._light_control.set_kelvin_color(kelvin))

    def update(self):
        """Fetch new state data for this light."""
        from pytradfri import RequestTimeout
        try:
            self._api(self._light.update())
        except RequestTimeout as exception:
            _LOGGER.warning("Tradfri update request timed out: %s", exception)

        # Handle Hue lights paired with the gateway
        # hex_color is 0 when bulb is unreachable
        if self._light_data.hex_color not in (None, '0'):
            self._rgb_color = color_util.rgb_hex_to_rgb_list(
                self._light_data.hex_color)
