import requests
from django.conf import settings

BASE_URL = "https://distribution-xml.booking.com/json"

class BookingAPI:
    def __init__(self):
        self.auth = (
            settings.BOOKING_API_USERNAME,
            settings.BOOKING_API_PASSWORD
        )

    def _get(self, endpoint, params=None):
        r = requests.get(
            f"{BASE_URL}/{endpoint}",
            auth=self.auth,
            params=params,
            timeout=30
        )
        r.raise_for_status()
        return r.json()

    def _post(self, endpoint, payload):
        r = requests.post(
            f"{BASE_URL}/{endpoint}",
            auth=self.auth,
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        return r.json()

    def get_reservations(self, room_id):
        return self._get("reservations", {"room_id": room_id})

    def update_availability(self, payload):
        return self._post("availability", payload)

    def update_pricing(self, payload):
        return self._post("rates", payload)
