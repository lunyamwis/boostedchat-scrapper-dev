from django.test import TestCase
import requests
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramTests(TestCase):
    url = os.getenv("API_URL", "")

    def test_hiker_comment_likers_chunk_gql(self):
        payload = {"comment_id": "18069481925141410"}
        response = requests.post(f"{self.url}/instagram/comment-likers-chunk-gql/", json=payload)
        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)    
        
    def test_hiker_comments_chunk_gql(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/comments-chunk-gql/", json=payload)
        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)
        
    def test_hiker_comments_threaded(self):
        payload = {"comment_id": "18069481925141410","media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/comments-threaded-chunk-gql/", json=payload)
        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)
        
    def test_hiker_fbsearch_accounts_v2(self):
        payload = {"query": "john"}
        response = requests.post(f"{self.url}/instagram/fbsearch-accounts-v2/", json=payload)
        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_fbsearch_places_v1(self):
        payload = {"query": "New York"}
        response = requests.post(f"{self.url}/instagram/fbsearch-places-v1/", json=payload)
        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)
    
    def test_hiker_fbsearch_places_v2(self):
        payload = {"query": "New York"}
        response = requests.post(f"{self.url}/instagram/fbsearch-places-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_fbsearch_reels_v2(self):
        payload = {"query": "travel"}
        response = requests.post(f"{self.url}/instagram/fbsearch-reels-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)
    
    def test_hiker_fbsearch_tags_v1(self):
        payload = {"query": "nature"}
        response = requests.post(f"{self.url}/instagram/fbsearch-topsearch-hashtags-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_fbsearch_topsearch_v1(self):
        payload = {"query": "music"}
        response = requests.post(f"{self.url}/instagram/fbsearch-topsearch-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_fbsearch_topsearch_v2(self):
        payload = {"query": "music"}
        response = requests.post(f"{self.url}/instagram/fbsearch-topsearch-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_hashtag_by_name_v1(self):
        payload = {"hashtag_name": "sunset"}
        response = requests.post(f"{self.url}/instagram/hashtag-by-name-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_hashtag_by_name_v2(self):
        payload = {"hashtag_name": "sunset"}
        response = requests.post(f"{self.url}/instagram/hashtag-by-name-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_hashtag_medias_clips_v1(self):
        payload = {"hashtag_name": "sunset"}
        response = requests.post(f"{self.url}/instagram/hashtag-medias-clips-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_hashtag_medias_clips_v2(self):
        payload = {"hashtag_name": "sunset"}
        response = requests.post(f"{self.url}/instagram/hashtag-medias-clips-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_hashtag_medias_clips_chunk_v1(self):
        payload = {"hashtag_name": "sunset"}
        response = requests.post(f"{self.url}/instagram/hashtag-medias-clips-chunk-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)
    
    def test_hiker_hashtag_medias_recent_v2(self):
        payload = {"hashtag_name": "sunset"}
        response = requests.post(f"{self.url}/instagram/hashtag-medias-recent-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_hashtag_medias_top_chunk_v1(self):
        payload = {"hashtag_name": "sunset"}
        response = requests.post(f"{self.url}/instagram/hashtag-medias-top-chunk-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)
    
    def test_hiker_hashtag_medias_top_recent_chunk_v1(self):
        payload = {"hashtag_name": "sunset"}
        response = requests.post(f"{self.url}/instagram/hashtag-medias-top-recent-chunk-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)
    
    def test_hiker_highlight_by_id_v2(self):
        payload = {"highlight_id": "17962946782292946"}
        response = requests.post(f"{self.url}/instagram/highlight-by-id-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)
    
    def test_hiker_highlight_by_url_v1(self):
        payload = {"highlight_url": "https://www.instagram.com/stories/highlights/17962946782292946/"}
        response = requests.post(f"{self.url}/instagram/highlight-by-url-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_location_by_id_v1(self):
        payload = {"location_id": "102144055612704"}
        response = requests.post(f"{self.url}/instagram/location-by-id-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_location_guides_v1(self):
        payload = {"location_id": "102144055612704"}
        response = requests.post(f"{self.url}/instagram/location-guides-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_location_medias_recent_v1(self):
        payload = {"location_id": "102144055612704"}
        response = requests.post(f"{self.url}/instagram/location-medias-recent-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_location_medias_top_v1(self):
        payload = {"location_id": "102144055612704"}
        response = requests.post(f"{self.url}/instagram/location-medias-top-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_location_medias_top_chunk_v1(self):
        payload = {"location_id": "102144055612704"}
        response = requests.post(f"{self.url}/instagram/location-medias-top-chunk-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)


    def test_hiker_location_search_v1(self):
        payload = {"lat": 40.308068999856, "lng": 82.807897925377}
        response = requests.post(f"{self.url}/instagram/location-search-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)
    
    def test_hiker_media_by_code_v1(self):
        payload = {"media_code": "DN8Z8_tjlhf"}
        response = requests.post(f"{self.url}/instagram/media-by-code-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)
    
    def test_hiker_media_by_id_v1(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/media-by-id-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)
    
    def test_hiker_media_by_url_v1(self):
        payload = {"media_url": "https://www.instagram.com/p/DN8Z8_tjlhf/"}
        response = requests.post(f"{self.url}/instagram/media-by-url-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_code_from_pk_v1(self):
        payload = {"media_pk": "3709954335787866207"}
        response = requests.post(f"{self.url}/instagram/media-code-from-pk-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_comment_offensive_v2(self):
        payload = {"media_id": "3713194538346271692_27971835", "comment_text": "This is a test comment"}
        response = requests.post(f"{self.url}/instagram/media-comment-offensive-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_comments(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/media-comments/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_comments_chunk_v1(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/media-comments-chunk-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_comments_v2(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/media-comments-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_info_by_code_v2(self):
        payload = {"media_code": "DN8Z8_tjlhf"}
        response = requests.post(f"{self.url}/instagram/media-info-by-code-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_info_by_id_v2(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/media-info-by-id-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_info_by_url_v2(self):
        payload = {"media_url": "https://www.instagram.com/p/DN8Z8_tjlhf/"}
        response = requests.post(f"{self.url}/instagram/media-info-by-url-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_insight_v1(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/media-insight-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_likers_gql(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/media-likers-gql/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_likers_v1(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/media-likers-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_likers_v2(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/media-likers-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200) 
    
    def test_hiker_media_oembed_v1(self):
        payload = {"media_url": "https://www.instagram.com/p/DN8Z8_tjlhf/"}
        response = requests.post(f"{self.url}/instagram/media-oembed-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200) 
    
    def test_hiker_media_pk_from_code_v1(self):
        payload = {"media_code": "DN8Z8_tjlhf"}
        response = requests.post(f"{self.url}/instagram/media-pk-from-code-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_pk_from_url_v1(self):
        payload = {"media_url": "https://www.instagram.com/p/DN8Z8_tjlhf/"}
        response = requests.post(f"{self.url}/instagram/media-pk-from-url-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_template_v2(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/media-template-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_media_user_v1(self):
        payload = {"media_id": "3713194538346271692_27971835"}
        response = requests.post(f"{self.url}/instagram/media-user-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_save_media(self):
        payload = {"media_url": "https://www.instagram.com/p/DN8Z8_tjlhf/"}
        response = requests.post(f"{self.url}/instagram/save-media/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    
    def test_hiker_search_accounts_v2(self):
        payload = {"query": "john"}
        response = requests.post(f"{self.url}/instagram/search-accounts-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_search_hashtags_v1(self):
        payload = {"query": "nature"}
        response = requests.post(f"{self.url}/instagram/search-hashtags-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_search_hashtags_v2(self):
        payload = {"query": "nature"}
        response = requests.post(f"{self.url}/instagram/search-hashtags-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_search_music_v1(self):
        payload = {"query": "pop"}
        response = requests.post(f"{self.url}/instagram/search-music-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_search_music_v2(self):
        payload = {"query": "pop"}
        response = requests.post(f"{self.url}/instagram/search-music-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_search_places_v2(self):
        payload = {"query": "New York"}
        response = requests.post(f"{self.url}/instagram/search-places-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_search_reels_v2(self):
        payload = {"query": "funny"}
        response = requests.post(f"{self.url}/instagram/search-reels-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_search_users_v1(self):
        payload = {"query": "john"}
        response = requests.post(f"{self.url}/instagram/search-users-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_search_topsearch_v2(self):
        payload = {"query": "travel"}
        response = requests.post(f"{self.url}/instagram/search-topsearch-v2/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_share_by_code_v1(self):
        payload = {"media_code": "DN8Z8_tjlhf"}
        response = requests.post(f"{self.url}/instagram/share-by-code-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_share_by_url_v1(self):
        payload = {"media_url": "https://www.instagram.com/p/DN8Z8_tjlhf/"}
        response = requests.post(f"{self.url}/instagram/share-by-url-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_hiker_share_reel_by_url_v1(self):
        payload = {"reel_url": "https://www.instagram.com/reel/CqZ2KX3Lh8D/"}
        response = requests.post(f"{self.url}/instagram/share-reel-by-url-v1/", json=payload)

        if response.status_code != 200:
            self.fail(f"Expected status 200 but got {response.status_code}. Response JSON: {response.json()}")
        self.assertEqual(response.status_code, 200)

