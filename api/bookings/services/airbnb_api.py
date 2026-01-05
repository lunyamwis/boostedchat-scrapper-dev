import requests
from django.conf import settings

BASE_URL = "https://api.airbnb.com/v2"

class AirbnbAPI:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {settings.AIRBNB_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

    def get_reservations(self, listing_id):
        r = requests.get(f"{BASE_URL}/reservations?listing_id={listing_id}", headers=self.headers)
        r.raise_for_status()
        return r.json().get("reservations", [])

    def update_availability(self, listing_id, date, available):
        payload = {"date": date.isoformat(), "available": available}
        r = requests.put(f"{BASE_URL}/calendar/{listing_id}", json=payload, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def update_pricing(self, listing_id, date, price):
        payload = {"date": date.isoformat(), "price": float(price)}
        r = requests.put(f"{BASE_URL}/pricing/{listing_id}", json=payload, headers=self.headers)
        r.raise_for_status()
        return r.json()

    def send_message(self, reservation_id: str, message: str):
        """
        Sends a message to the guest of a reservation
        """
        url = f"{self.BASE_URL}/messages"

        payload = {
            "reservation_id": reservation_id,
            "message": message
        }

        response = requests.post(url, json=payload, headers=self._headers())

        # Raise exception if request failed
        response.raise_for_status()

        return response.json()
