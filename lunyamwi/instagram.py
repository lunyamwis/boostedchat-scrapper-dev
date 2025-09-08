import requests
from typing import Any, Dict, List, Optional, Union

class InstagramClient:
    def __init__(self, base_url: str = "https://mqtt.staging.boostedchat.com"):
        self.base_url = base_url.rstrip("/")

    def _post(self, endpoint: str, payload: Union[Dict, List, None] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def _get(self, endpoint: str) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    # -------- Accounts --------
    def login(self, igname: str):
        return self._post("/login", {"igname": igname})

    def logout(self, igname: str):
        return self._post("/accounts/logout", {"igname": igname})

    def is_logged_in(self, igname: str):
        return self._post("/accounts/isloggedin", {"igname": igname})

    def disconnect(self, igname: str):
        return self._post("/accounts/disconnect", {"igname": igname})

    # -------- Messaging --------
    def send_message(self, message: str, username_from: str, username_to: str):
        return self._post("/send-message", {
            "message": message,
            "username_from": username_from,
            "username_to": username_to
        })

    def send_media_message(self, message: str, username_from: str, username_to: str,
                           links: str, media_id: str):
        return self._post("/send-first-media-message", {
            "message": message,
            "username_from": username_from,
            "username_to": username_to,
            "links": links,
            "mediaId": media_id
        })

    # -------- Media --------
    def post_media(self, image_url: str, caption: str, username_from: str):
        return self._post("/post-media", {
            "imageURL": image_url,
            "caption": caption,
            "username_from": username_from
        })

    def like_media(self, media_id: str, username_from: str):
        return self._post("/like", {
            "mediaId": media_id,
            "username_from": username_from
        })

    def comment_media(self, media_id: str, comment: str, username_from: str):
        return self._post("/comment", [{
            "mediaId": media_id,
            "comment": comment,
            "username_from": username_from
        }])

    def follow(self, username_from: str, username_to: str):
        return self._post("/follow", [{
            "usernames_to": username_to,
            "username_from": username_from
        }])

    def unfollow(self, username_from: str, username_to: str):
        return self._post("/unfollow", [{
            "usernames_to": username_to,
            "username_from": username_from
        }])

    # -------- Stories --------
    def view_story(self, username_from: str, username_to: str):
        return self._post("/viewStory", [{
            "usernames_to": username_to,
            "username_from": username_from
        }])

    def react_to_story(self, username_from: str, username_to: str):
        return self._post("/reactToStory", [{
            "usernames_to": username_to,
            "username_from": username_from
        }])

    # -------- Health --------
    def health(self):
        return self._get("/health")
    

# Example usage
def instagram_client(base_url: Optional[str] = None) -> InstagramClient:
    """Create an Instagram API client instance"""
    return InstagramClient(base_url)