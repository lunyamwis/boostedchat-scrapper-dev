import requests

class CanvaAPI:
    BASE_URL = "https://api.canva.com/v1"

    def __init__(self, app):
        self.access_token = app.access_token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def insert_text_element(self, design_id, text):
        url = f"{self.BASE_URL}/designs/{design_id}/elements"
        payload = {"type": "text", "text": text}
        r = requests.post(url, json=payload, headers=self._headers())
        r.raise_for_status()
        return r.json()

    def update_text(self, design_id, text):
        url = f"{self.BASE_URL}/designs/{design_id}/update_text"
        payload = {"text": text}
        r = requests.post(url, json=payload, headers=self._headers())
        r.raise_for_status()
        return r.json()

    def export_design(self, design_id):
        url = f"{self.BASE_URL}/designs/{design_id}/export"
        r = requests.post(url, headers=self._headers())
        r.raise_for_status()
        return r.json().get("file_url")

    def apply_brand(self, design_id, brand_kit_id):
        url = f"{self.BASE_URL}/designs/{design_id}/apply_brand"
        payload = {"brand_kit_id": brand_kit_id}
        r = requests.post(url, json=payload, headers=self._headers())
        r.raise_for_status()
        return r.json()
