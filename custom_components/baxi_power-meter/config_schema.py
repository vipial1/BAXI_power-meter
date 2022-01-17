import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.const import CONF_NAME, CONF_USERNAME, CONF_PASSWORD
from .const import (
    DEFAULT_NAME,
)

CONF_PERIOD1 = "P1"
CONF_PERIOD2 = "P2"
CONF_PERIOD3 = "P3"


USER_SCHEMA = {
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
}

PERIODS_SCHEMA = {
    vol.Optional(CONF_PERIOD1): cv.string,
    vol.Optional(CONF_PERIOD2): cv.string,
    vol.Optional(CONF_PERIOD3): cv.string,
}
