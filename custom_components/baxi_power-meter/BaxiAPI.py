import requests
from datetime import datetime, timedelta
import logging
from .const import DEVICE_ID_KEY

_LOGGER = logging.getLogger(__name__)


class BaxiAPI:
    BASE_URL = "https://api.helki.com"
    BASE_HEADER = {
        "Accept": "application/json, text/plain, */*",
        "Connection": "keep-alive",
        "X-Requested-With": "es.baxi.controlalec",
        "Content-Type": "application/x-www-form-urlencoded",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Accept-Encoding": "gzip, deflate",
        "Authorization": "Basic NTRiY2NiZmI0MWE5YTUxMTNmMDQ4OGQwOnZkaXZkaQ==",
    }
    DEVICE_ENDPOINT_KEYWORD = "__device_here__"
    endpoints = {
        "TOKEN": BASE_URL + "/client/token",
        "SAMPLES": BASE_URL + f"/api/v2/devs/{DEVICE_ENDPOINT_KEYWORD}/pmo/2/samples",
        "DEVICES": BASE_URL + "/api/v2/grouped_devs",
    }

    def __init__(self, hass, user, password):
        self.hass = hass
        self._bootstraped = False
        self._user = user
        self._password = password
        self._access_token = None
        self._refresh_token = None
        self._expiration_time = None
        self._token_duration = 0

    async def bootstrap(self):
        if self._bootstraped:
            return

        await self._login()
        await self._load_device_information()
        self._bootstraped = True

    async def _login(self):
        api_endpoint = self.endpoints["TOKEN"]
        payload = {
            "grant_type": "password",
            "username": self._user,
            "password": self._password,
        }
        await self._post_token(api_endpoint, payload)

    async def _post_token(self, api_endpoint, payload):
        response = await self.async_post_request(endpoint=api_endpoint, payload=payload)
        if not response:
            logging.error("ERROR logging to BAXI. Perhaps wrong password/token??")
            raise Exception("ERROR logging to BAXI. Perhaps wrong password/token??")

        response_json = response.json()
        self._access_token = response_json.get("access_token", None)
        self._refresh_token = response_json.get("refresh_token", None)
        self._token_duration = int(response_json.get("expires_in", 0))
        self._expiration_time = datetime.now() + timedelta(seconds=self._token_duration)

    def _need_refresh_token(self, payload):
        if not self._refresh_token:
            # Nothing to refresh
            return False
        grant_type = payload.get("grant_type", None) if payload else None
        if grant_type and grant_type == "refresh_token":
            # We are already refreshing
            return False
        desired_remaining_time = self._token_duration / 2
        return (self._expiration_time - datetime.now()) < timedelta(
            seconds=desired_remaining_time
        )

    async def _async_get_new_token(self):
        if not self._refresh_token:
            return await self._login()

        api_endpoint = self.endpoints["TOKEN"]
        payload = {"grant_type": "refresh_token", "refresh_token": self._refresh_token}
        await self._post_token(api_endpoint, payload)

    def _sync_request(self, request, url, headers, payload=None):
        try:
            if request == "get":
                response = requests.get(url=url, headers=headers)
            elif request == "put":
                response = requests.put(url=url, data=payload, headers=headers)
            elif request == "post":
                response = requests.post(url=url, data=payload, headers=headers)
        except Exception as e:
            _LOGGER.exception(f"EXCEPTION with {request} request to {url}:", e)
            raise e

        if not response.ok:
            _LOGGER.error(
                f"ERROR with {request} request to {url}: {response.status_code}"
            )
            return None
        return response

    async def _async_request(self, method, endpoint, headers, payload):
        if self._need_refresh_token(payload):
            await self._async_get_new_token()

        return await self.hass.async_add_executor_job(
            self._sync_request, method, endpoint, headers, payload
        )

    async def async_post_request(self, endpoint, payload, headers=BASE_HEADER):
        if self._access_token and endpoint != self.endpoints["TOKEN"]:
            headers = headers.copy()
            headers["Authorization"] = f"Bearer {self._access_token}"
        return await self._async_request("post", endpoint, headers, payload)

    async def async_put_request(self, endpoint, payload, headers=BASE_HEADER):
        return await self._async_request("put", endpoint, headers, payload)

    async def async_get_request(self, endpoint, headers=BASE_HEADER):

        headers = headers.copy()
        headers["Authorization"] = f"Bearer {self._access_token}"

        response = await self._async_request("get", endpoint, headers, None)

        return response.json() if response else response

    async def _load_device_information(self):
        api_endpoint = self.endpoints.get("DEVICES")

        dev_info = await self.async_get_request(api_endpoint)
        self.info = dev_info[0]["devs"][0]  # Single device supported currently

    def get_device_information(self):
        return self.info

    def is_bootstraped(self):
        return self._bootstraped

    async def get_samples_between_dates(self, initial_datetime, end_datetime):
        api_endpoint = self.endpoints.get("SAMPLES")
        api_endpoint = api_endpoint.replace(
            self.DEVICE_ENDPOINT_KEYWORD,
            self.get_device_information().get(DEVICE_ID_KEY),
        )
        api_endpoint = api_endpoint + f"?start={initial_datetime}&end={end_datetime}"

        response = await self.async_get_request(api_endpoint)

        return response["samples"]
