import requests
import logging
import os
from typing import Optional, Dict, Any, List, Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramDataClient:
    """Instagram Data API client for accessing Instagram data through various endpoints"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("API_URL", "")
        if not self.base_url:
            raise ValueError("API_URL must be provided either as parameter or environment variable")
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the Instagram API endpoint"""
        try:
            url = f"{self.base_url}/instagram/{endpoint}/"
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Success: {endpoint} - {response.status_code}")
            return {
                "success": True,
                "data": result,
                "status_code": response.status_code
            }
        except requests.RequestException as e:
            logger.error(f"Error in {endpoint}: {e}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None),
                "response": getattr(e.response, 'text', None) if hasattr(e, 'response') else None
            }
    
    # Comment and Engagement Methods
    def get_comment_likers_chunk_gql(self, comment_id: str, max_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comment likers using GraphQL chunked approach"""
        payload = {"comment_id": comment_id}
        if max_id:
            payload["max_id"] = max_id
        return self._make_request("comment-likers-chunk-gql", payload)
    
    def get_comments_chunk_gql(self, media_id: str, max_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comments using GraphQL chunked approach"""
        payload = {"media_id": media_id}
        if max_id:
            payload["max_id"] = max_id
        return self._make_request("comments-chunk-gql", payload)
    
    def get_comments_threaded_chunk_gql(self, comment_id: str, media_id: str, max_id: Optional[str] = None) -> Dict[str, Any]:
        """Get threaded comments using GraphQL chunked approach"""
        payload = {
            "comment_id": comment_id,
            "media_id": media_id
        }
        if max_id:
            payload["max_id"] = max_id
        return self._make_request("comments-threaded-chunk-gql", payload)
    
    # Facebook Search Methods
    def fbsearch_accounts_v2(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search accounts using Facebook search v2"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("fbsearch-accounts-v2", payload)
    
    def fbsearch_places_v1(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search places using Facebook search v1"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("fbsearch-places-v1", payload)
    
    def fbsearch_places_v2(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search places using Facebook search v2"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("fbsearch-places-v2", payload)
    
    def fbsearch_reels_v2(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search reels using Facebook search v2"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("fbsearch-reels-v2", payload)
    
    def fbsearch_topsearch_hashtags_v1(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search hashtags in top search v1"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("fbsearch-topsearch-hashtags-v1", payload)
    
    def fbsearch_topsearch_v1(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Top search using Facebook search v1"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("fbsearch-topsearch-v1", payload)
    
    def fbsearch_topsearch_v2(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Top search using Facebook search v2"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("fbsearch-topsearch-v2", payload)
    
    # Hashtag Methods
    def get_hashtag_by_name_v1(self, hashtag_name: str) -> Dict[str, Any]:
        """Get hashtag information by name v1"""
        payload = {"hashtag_name": hashtag_name}
        return self._make_request("hashtag-by-name-v1", payload)
    
    def get_hashtag_by_name_v2(self, hashtag_name: str) -> Dict[str, Any]:
        """Get hashtag information by name v2"""
        payload = {"hashtag_name": hashtag_name}
        return self._make_request("hashtag-by-name-v2", payload)
    
    def get_hashtag_medias_clips_v1(self, hashtag_name: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get clips for hashtag v1"""
        payload = {"hashtag_name": hashtag_name}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("hashtag-medias-clips-v1", payload)
    
    def get_hashtag_medias_clips_v2(self, hashtag_name: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get clips for hashtag v2"""
        payload = {"hashtag_name": hashtag_name}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("hashtag-medias-clips-v2", payload)
    
    def get_hashtag_medias_clips_chunk_v1(self, hashtag_name: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get clips for hashtag chunked v1"""
        payload = {"hashtag_name": hashtag_name}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("hashtag-medias-clips-chunk-v1", payload)
    
    def get_hashtag_medias_recent_v2(self, hashtag_name: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get recent media for hashtag v2"""
        payload = {"hashtag_name": hashtag_name}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("hashtag-medias-recent-v2", payload)
    
    def get_hashtag_medias_top_chunk_v1(self, hashtag_name: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get top media for hashtag chunked v1"""
        payload = {"hashtag_name": hashtag_name}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("hashtag-medias-top-chunk-v1", payload)
    
    def get_hashtag_medias_top_recent_chunk_v1(self, hashtag_name: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get top and recent media for hashtag chunked v1"""
        payload = {"hashtag_name": hashtag_name}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("hashtag-medias-top-recent-chunk-v1", payload)
    
    # Highlight Methods
    def get_highlight_by_id_v2(self, highlight_id: str) -> Dict[str, Any]:
        """Get highlight by ID v2"""
        payload = {"highlight_id": highlight_id}
        return self._make_request("highlight-by-id-v2", payload)
    
    def get_highlight_by_url_v1(self, highlight_url: str) -> Dict[str, Any]:
        """Get highlight by URL v1"""
        payload = {"highlight_url": highlight_url}
        return self._make_request("highlight-by-url-v1", payload)
    
    # Location Methods
    def get_location_by_id_v1(self, location_id: str) -> Dict[str, Any]:
        """Get location information by ID v1"""
        payload = {"location_id": location_id}
        return self._make_request("location-by-id-v1", payload)
    
    def get_location_guides_v1(self, location_id: str) -> Dict[str, Any]:
        """Get location guides v1"""
        payload = {"location_id": location_id}
        return self._make_request("location-guides-v1", payload)
    
    def get_location_medias_recent_v1(self, location_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get recent media for location v1"""
        payload = {"location_id": location_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("location-medias-recent-v1", payload)
    
    def get_location_medias_top_v1(self, location_id: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Get top media for location v1"""
        payload = {"location_id": location_id}
        if count:
            payload["count"] = count
        return self._make_request("location-medias-top-v1", payload)
    
    def get_location_medias_top_chunk_v1(self, location_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get top media for location chunked v1"""
        payload = {"location_id": location_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("location-medias-top-chunk-v1", payload)
    
    def search_location_v1(self, lat: float, lng: float, count: Optional[int] = None) -> Dict[str, Any]:
        """Search locations by coordinates v1"""
        payload = {"lat": lat, "lng": lng}
        if count:
            payload["count"] = count
        return self._make_request("location-search-v1", payload)
    
    # Media Methods
    def get_media_by_code_v1(self, media_code: str) -> Dict[str, Any]:
        """Get media information by code v1"""
        payload = {"media_code": media_code}
        return self._make_request("media-by-code-v1", payload)
    
    def get_media_by_id_v1(self, media_id: str) -> Dict[str, Any]:
        """Get media information by ID v1"""
        payload = {"media_id": media_id}
        return self._make_request("media-by-id-v1", payload)
    
    def get_media_by_url_v1(self, media_url: str) -> Dict[str, Any]:
        """Get media information by URL v1"""
        payload = {"media_url": media_url}
        return self._make_request("media-by-url-v1", payload)
    
    def get_media_code_from_pk_v1(self, media_pk: str) -> Dict[str, Any]:
        """Get media code from PK v1"""
        payload = {"media_pk": media_pk}
        return self._make_request("media-code-from-pk-v1", payload)
    
    def check_media_comment_offensive_v2(self, media_id: str, comment_text: str) -> Dict[str, Any]:
        """Check if comment text is offensive v2"""
        payload = {"media_id": media_id, "comment_text": comment_text}
        return self._make_request("media-comment-offensive-v2", payload)
    
    def get_media_comments(self, media_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get media comments"""
        payload = {"media_id": media_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("media-comments", payload)
    
    def get_media_comments_chunk_v1(self, media_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get media comments chunked v1"""
        payload = {"media_id": media_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("media-comments-chunk-v1", payload)
    
    def get_media_comments_v2(self, media_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get media comments v2"""
        payload = {"media_id": media_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("media-comments-v2", payload)
    
    def get_media_info_by_code_v2(self, media_code: str) -> Dict[str, Any]:
        """Get detailed media information by code v2"""
        payload = {"media_code": media_code}
        return self._make_request("media-info-by-code-v2", payload)
    
    def get_media_info_by_id_v2(self, media_id: str) -> Dict[str, Any]:
        """Get detailed media information by ID v2"""
        payload = {"media_id": media_id}
        return self._make_request("media-info-by-id-v2", payload)
    
    def get_media_info_by_url_v2(self, media_url: str) -> Dict[str, Any]:
        """Get detailed media information by URL v2"""
        payload = {"media_url": media_url}
        return self._make_request("media-info-by-url-v2", payload)
    
    def get_media_insight_v1(self, media_id: str) -> Dict[str, Any]:
        """Get media insights v1"""
        payload = {"media_id": media_id}
        return self._make_request("media-insight-v1", payload)
    
    def get_media_likers_gql(self, media_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get media likers using GraphQL"""
        payload = {"media_id": media_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("media-likers-gql", payload)
    
    def get_media_likers_v1(self, media_id: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Get media likers v1"""
        payload = {"media_id": media_id}
        if count:
            payload["count"] = count
        return self._make_request("media-likers-v1", payload)
    
    def get_media_likers_v2(self, media_id: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Get media likers v2"""
        payload = {"media_id": media_id}
        if count:
            payload["count"] = count
        return self._make_request("media-likers-v2", payload)
    
    def get_media_oembed_v1(self, media_url: str) -> Dict[str, Any]:
        """Get media oEmbed data v1"""
        payload = {"media_url": media_url}
        return self._make_request("media-oembed-v1", payload)
    
    def get_media_pk_from_code_v1(self, media_code: str) -> Dict[str, Any]:
        """Get media PK from code v1"""
        payload = {"media_code": media_code}
        return self._make_request("media-pk-from-code-v1", payload)
    
    def get_media_pk_from_url_v1(self, media_url: str) -> Dict[str, Any]:
        """Get media PK from URL v1"""
        payload = {"media_url": media_url}
        return self._make_request("media-pk-from-url-v1", payload)
    
    def get_media_template_v2(self, media_id: str) -> Dict[str, Any]:
        """Get media template v2"""
        payload = {"media_id": media_id}
        return self._make_request("media-template-v2", payload)
    
    def get_media_user_v1(self, media_id: str) -> Dict[str, Any]:
        """Get media user information v1"""
        payload = {"media_id": media_id}
        return self._make_request("media-user-v1", payload)
    
    def save_media(self, media_url: str) -> Dict[str, Any]:
        """Save media"""
        payload = {"media_url": media_url}
        return self._make_request("save-media", payload)
    
    # Search Methods
    def search_accounts_v2(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search accounts v2"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("search-accounts-v2", payload)
    
    def search_hashtags_v1(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search hashtags v1"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("search-hashtags-v1", payload)
    
    def search_hashtags_v2(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search hashtags v2"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("search-hashtags-v2", payload)
    
    def search_music_v1(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search music v1"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("search-music-v1", payload)
    
    def search_music_v2(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search music v2"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("search-music-v2", payload)
    
    def search_places_v2(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search places v2"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("search-places-v2", payload)
    
    def search_reels_v2(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search reels v2"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("search-reels-v2", payload)
    
    def search_users_v1(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search users v1"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("search-users-v1", payload)
    
    def search_topsearch_v2(self, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Top search v2"""
        payload = {"query": query}
        if count:
            payload["count"] = count
        return self._make_request("search-topsearch-v2", payload)
    
    # Share Methods
    def share_by_code_v1(self, media_code: str) -> Dict[str, Any]:
        """Share media by code v1"""
        payload = {"media_code": media_code}
        return self._make_request("share-by-code-v1", payload)
    
    def share_by_url_v1(self, media_url: str) -> Dict[str, Any]:
        """Share media by URL v1"""
        payload = {"media_url": media_url}
        return self._make_request("share-by-url-v1", payload)
    
    def share_reel_by_url_v1(self, reel_url: str) -> Dict[str, Any]:
        """Share reel by URL v1"""
        payload = {"reel_url": reel_url}
        return self._make_request("share-reel-by-url-v1", payload)
    
    # Story Methods
    def get_story_by_id_v1(self, story_id: str) -> Dict[str, Any]:
        """Get story by ID v1"""
        payload = {"story_id": story_id}
        return self._make_request("story-by-id-v1", payload)
    
    def get_story_by_url_v1(self, story_url: str) -> Dict[str, Any]:
        """Get story by URL v1"""
        payload = {"story_url": story_url}
        return self._make_request("story-by-url-v1", payload)
    
    def get_story_by_url_v2(self, story_url: str) -> Dict[str, Any]:
        """Get story by URL v2"""
        payload = {"story_url": story_url}
        return self._make_request("story-by-url-v2", payload)
    
    def download_story_by_story_url_v1(self, story_url: str) -> Dict[str, Any]:
        """Download story by story URL v1"""
        payload = {"story_url": story_url}
        return self._make_request("story-download-by-story-url-v1", payload)
    
    def download_story_by_url_v1(self, story_url: str) -> Dict[str, Any]:
        """Download story by URL v1"""
        payload = {"story_url": story_url}
        return self._make_request("story-download-by-url-v1", payload)
    
    def download_story_v1(self, story_id: str) -> Dict[str, Any]:
        """Download story v1"""
        payload = {"story_id": story_id}
        return self._make_request("story-download-v1", payload)
    
    # Track/Music Methods
    def get_track_by_canonical_id_v2(self, canonical_id: str) -> Dict[str, Any]:
        """Get track by canonical ID v2"""
        payload = {"canonical_id": canonical_id}
        return self._make_request("track-by-canonical-id-v2", payload)
    
    def get_track_by_id_v2(self, track_id: str) -> Dict[str, Any]:
        """Get track by ID v2"""
        payload = {"track_id": track_id}
        return self._make_request("track-by-id-v2", payload)
    
    def get_track_stream_by_id_v2(self, track_id: str) -> Dict[str, Any]:
        """Get track stream by ID v2"""
        payload = {"track_id": track_id}
        return self._make_request("track-stream-by-id-v2", payload)
    
    # User Methods
    def get_user_a2(self, user_id: str) -> Dict[str, Any]:
        """Get user A2 data"""
        payload = {"user_id": user_id}
        return self._make_request("user-a2", payload)
    
    def get_user_about_v1(self, user_id: str) -> Dict[str, Any]:
        """Get user about information v1"""
        payload = {"user_id": user_id}
        return self._make_request("user-about-v1", payload)
    
    def get_user_by_id_v1(self, user_id: str) -> Dict[str, Any]:
        """Get user information by ID v1"""
        payload = {"user_id": user_id}
        return self._make_request("user-by-id-v1", payload)
    
    def get_user_by_id_v2(self, user_id: str) -> Dict[str, Any]:
        """Get user information by ID v2"""
        payload = {"user_id": user_id}
        return self._make_request("user-by-id-v2", payload)
    
    def get_user_by_url_v1(self, user_url: str) -> Dict[str, Any]:
        """Get user information by URL v1"""
        payload = {"user_url": user_url}
        return self._make_request("user-by-url-v1", payload)
    
    def get_user_by_username_v1(self, username: str) -> Dict[str, Any]:
        """Get user information by username v1"""
        payload = {"username": username}
        return self._make_request("user-by-username-v1", payload)
    
    def get_user_by_username_v2(self, username: str) -> Dict[str, Any]:
        """Get user information by username v2"""
        payload = {"username": username}
        return self._make_request("user-by-username-v2", payload)
    
    def get_user_clips_v2(self, user_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get user clips v2"""
        payload = {"user_id": user_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("user-clips-v2", payload)
    
    def get_user_explore_businesses_by_id_v2(self, user_id: str) -> Dict[str, Any]:
        """Get user explore businesses by ID v2"""
        payload = {"user_id": user_id}
        return self._make_request("user-explore-businesses-by-id-v2", payload)
    
    def get_user_followers_chunk_gql(self, user_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get user followers chunked using GraphQL"""
        payload = {"user_id": user_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("user-followers-chunk-gql", payload)
    
    def get_user_followers_chunk_v1(self, user_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get user followers chunked v1"""
        payload = {"user_id": user_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("user-followers-chunk-v1", payload)
    
    def get_user_following(self, user_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get user following"""
        payload = {"user_id": user_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("user-following", payload)
    
    def get_user_following_chunk_gql(self, user_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get user following chunked using GraphQL"""
        payload = {"user_id": user_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("user-following-chunk-gql", payload)
    
    def get_user_following_chunk_v1(self, user_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get user following chunked v1"""
        payload = {"user_id": user_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("user-following-chunk-v1", payload)
    
    def get_user_highlights(self, user_id: str) -> Dict[str, Any]:
        """Get user highlights"""
        payload = {"user_id": user_id}
        return self._make_request("user-highlights", payload)
    
    def get_user_highlights_by_username_v1(self, username: str) -> Dict[str, Any]:
        """Get user highlights by username v1"""
        payload = {"username": username}
        return self._make_request("user-highlights-by-username-v1", payload)
    
    def get_user_highlights_by_username_v2(self, username: str) -> Dict[str, Any]:
        """Get user highlights by username v2"""
        payload = {"username": username}
        return self._make_request("user-highlights-by-username-v2", payload)
    
    def get_user_highlights_v1(self, user_id: str) -> Dict[str, Any]:
        """Get user highlights v1"""
        payload = {"user_id": user_id}
        return self._make_request("user-highlights-v1", payload)
    
    def get_user_highlights_v2(self, user_id: str) -> Dict[str, Any]:
        """Get user highlights v2"""
        payload = {"user_id": user_id}
        return self._make_request("user-highlights-v2", payload)
    
    def get_user_medias(self, user_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get user medias"""
        payload = {"user_id": user_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("user-medias", payload)
    
    def get_user_medias_chunk_v1(self, user_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get user medias chunked v1"""
        payload = {"user_id": user_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("user-medias-chunk-v1", payload)
    
    def get_user_medias_pinned_v1(self, user_id: str) -> Dict[str, Any]:
        """Get user pinned medias v1"""
        payload = {"user_id": user_id}
        return self._make_request("user-medias-pinned-v1", payload)
    
    def get_user_medias_v2(self, user_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get user medias v2"""
        payload = {"user_id": user_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("user-medias-v2", payload)
    
    def get_user_related_profiles_gql(self, user_id: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Get user related profiles using GraphQL"""
        payload = {"user_id": user_id}
        if count:
            payload["count"] = count
        return self._make_request("user-related-profiles-gql", payload)
    
    def search_user_followers_v1(self, user_id: str, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search user followers v1"""
        payload = {"user_id": user_id, "query": query}
        if count:
            payload["count"] = count
        return self._make_request("user-search-followers-v1", payload)
    
    def search_user_following_v1(self, user_id: str, query: str, count: Optional[int] = None) -> Dict[str, Any]:
        """Search user following v1"""
        payload = {"user_id": user_id, "query": query}
        if count:
            payload["count"] = count
        return self._make_request("user-search-following-v1", payload)
    
    def get_user_stories_by_username_v1(self, username: str) -> Dict[str, Any]:
        """Get user stories by username v1"""
        payload = {"username": username}
        return self._make_request("user-stories-by-username-v1", payload)
    
    def get_user_stories_by_username_v2(self, username: str) -> Dict[str, Any]:
        """Get user stories by username v2"""
        payload = {"username": username}
        return self._make_request("user-stories-by-username-v2", payload)
    
    def get_user_stories_v1(self, user_id: str) -> Dict[str, Any]:
        """Get user stories v1"""
        payload = {"user_id": user_id}
        return self._make_request("user-stories-v1", payload)
    
    def get_user_stories_v2(self, user_id: str) -> Dict[str, Any]:
        """Get user stories v2"""
        payload = {"user_id": user_id}
        return self._make_request("user-stories-v2", payload)
    
    def get_user_tag_medias_chunk_v1(self, user_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get media where user is tagged chunked v1"""
        payload = {"user_id": user_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("user-tag-medias-chunk-v1", payload)
    
    def get_user_tag_medias_v2(self, user_id: str, max_id: Optional[str] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """Get media where user is tagged v2"""
        payload = {"user_id": user_id}
        if max_id:
            payload["max_id"] = max_id
        if count:
            payload["count"] = count
        return self._make_request("user-tag-medias-v2", payload)
    
    def get_user_web_profile_info_v1(self, username: str) -> Dict[str, Any]:
        """Get user web profile info v1"""
        payload = {"username": username}
        return self._make_request("user-web-profile-info-v1", payload)
    
    def get_userstream_by_id_v2(self, user_id: str) -> Dict[str, Any]:
        """Get userstream by ID v2"""
        payload = {"user_id": user_id}
        return self._make_request("userstream-by-id-v2", payload)
    
    def get_userstream_by_username_v2(self, username: str) -> Dict[str, Any]:
        """Get userstream by username v2"""
        payload = {"username": username}
        return self._make_request("userstream-by-username-v2", payload)


# Convenience function
def instagram_data_client(base_url: Optional[str] = None) -> InstagramDataClient:
    """Create an Instagram Data API client instance"""
    return InstagramDataClient(base_url)


# Interactive helper functions
def search_instagram_interactive(client: InstagramDataClient) -> Dict[str, Any]:
    """Interactive function to search Instagram"""
    search_type = input("What do you want to search? (accounts/hashtags/places/reels/music/users/topsearch): ").strip().lower()
    query = input("Enter search query: ").strip()
    count = input("Enter count (optional): ").strip()
    
    if not query:
        return {
            "success": False,
            "error": "Search query is required"
        }
    
    count_val = int(count) if count.isdigit() else None
    
    if search_type == "accounts":
        return client.search_accounts_v2(query, count_val)
    elif search_type == "hashtags":
        return client.search_hashtags_v2(query, count_val)
    elif search_type == "places":
        return client.search_places_v2(query, count_val)
    elif search_type == "reels":
        return client.search_reels_v2(query, count_val)
    elif search_type == "music":
        return client.search_music_v2(query, count_val)
    elif search_type == "users":
        return client.search_users_v1(query, count_val)
    elif search_type == "topsearch":
        return client.search_topsearch_v2(query, count_val)
    else:
        return {
            "success": False,
            "error": "Invalid search type. Choose from: accounts, hashtags, places, reels, music, users, topsearch"
        }


def get_user_data_interactive(client: InstagramDataClient) -> Dict[str, Any]:
    """Interactive function to get comprehensive user data"""
    username = input("Enter Instagram username: ").strip()
    if not username:
        return {
            "success": False,
            "error": "Username is required"
        }
    
    # Get user info first
    user_info = client.get_user_by_username_v2(username)
    if not user_info["success"]:
        return user_info
    
    # Extract user ID from response (handle different response formats)
    user_data = user_info.get("data", {})
    user_id = None
    if isinstance(user_data, dict):
        user_id = user_data.get("user_id") or user_data.get("id") or user_data.get("pk")
    
    if not user_id:
        print("Warning: Could not extract user ID. Some endpoints may not work.")
        user_id = input("Enter user ID manually (or press Enter to skip): ").strip()
    
    results = {
        "user_info": user_info,
        "web_profile": client.get_user_web_profile_info_v1(username),
        "highlights_by_username": client.get_user_highlights_by_username_v2(username),
        "stories_by_username": client.get_user_stories_by_username_v2(username)
    }
    
    if user_id:
        results.update({
            "medias": client.get_user_medias_v2(user_id, count=12),
            "clips": client.get_user_clips_v2(user_id, count=12),
            "highlights": client.get_user_highlights_v2(user_id),
            "stories": client.get_user_stories_v2(user_id),
            "tagged_medias": client.get_user_tag_medias_v2(user_id, count=12),
            "pinned_medias": client.get_user_medias_pinned_v1(user_id)
        })
    
    return results


def get_hashtag_data_interactive(client: InstagramDataClient) -> Dict[str, Any]:
    """Interactive function to get comprehensive hashtag data"""
    hashtag = input("Enter hashtag name (without #): ").strip()
    if not hashtag:
        return {
            "success": False,
            "error": "Hashtag is required"
        }
    
    results = {
        "hashtag_info": client.get_hashtag_by_name_v2(hashtag),
        "recent_media": client.get_hashtag_medias_recent_v2(hashtag, count=20),
        "clips_v2": client.get_hashtag_medias_clips_v2(hashtag, count=20),
        "clips_chunk": client.get_hashtag_medias_clips_chunk_v1(hashtag, count=20),
        "top_chunk": client.get_hashtag_medias_top_chunk_v1(hashtag, count=20),
        "top_recent_chunk": client.get_hashtag_medias_top_recent_chunk_v1(hashtag, count=20)
    }
    
    return results


def get_media_data_interactive(client: InstagramDataClient) -> Dict[str, Any]:
    """Interactive function to get comprehensive media data"""
    input_type = input("Enter 'url' for Instagram URL, 'code' for shortcode, or 'id' for media ID: ").strip().lower()
    
    if input_type == "url":
        url = input("Enter Instagram post URL: ").strip()
        if not url:
            return {
                "success": False,
                "error": "URL is required"
            }
        
        results = {
            "media_by_url": client.get_media_by_url_v1(url),
            "media_info_by_url": client.get_media_info_by_url_v2(url),
            "media_oembed": client.get_media_oembed_v1(url),
            "media_pk_from_url": client.get_media_pk_from_url_v1(url),
            "share_by_url": client.share_by_url_v1(url)
        }
        
    elif input_type == "code":
        code = input("Enter Instagram post shortcode: ").strip()
        if not code:
            return {
                "success": False,
                "error": "Shortcode is required"
            }
        
        results = {
            "media_by_code": client.get_media_by_code_v1(code),
            "media_info_by_code": client.get_media_info_by_code_v2(code),
            "media_pk_from_code": client.get_media_pk_from_code_v1(code),
            "share_by_code": client.share_by_code_v1(code)
        }
        
    elif input_type == "id":
        media_id = input("Enter Instagram media ID: ").strip()
        if not media_id:
            return {
                "success": False,
                "error": "Media ID is required"
            }
        
        results = {
            "media_by_id": client.get_media_by_id_v1(media_id),
            "media_info_by_id": client.get_media_info_by_id_v2(media_id),
            "media_comments": client.get_media_comments_v2(media_id, count=20),
            "media_comments_chunk": client.get_media_comments_chunk_v1(media_id, count=20),
            "media_likers": client.get_media_likers_v2(media_id, count=20),
            "media_likers_gql": client.get_media_likers_gql(media_id, count=20),
            "media_insight": client.get_media_insight_v1(media_id),
            "media_template": client.get_media_template_v2(media_id),
            "media_user": client.get_media_user_v1(media_id)
        }
        
    else:
        return {
            "success": False,
            "error": "Invalid input type. Choose 'url', 'code', or 'id'"
        }
    
    return results


def get_location_data_interactive(client: InstagramDataClient) -> Dict[str, Any]:
    """Interactive function to get location data"""
    location_id = input("Enter location ID: ").strip()
    if not location_id:
        return {
            "success": False,
            "error": "Location ID is required"
        }
    
    results = {
        "location_info": client.get_location_by_id_v1(location_id),
        "location_guides": client.get_location_guides_v1(location_id),
        "recent_media": client.get_location_medias_recent_v1(location_id, count=20),
        "top_media": client.get_location_medias_top_v1(location_id, count=20),
        "top_media_chunk": client.get_location_medias_top_chunk_v1(location_id, count=20)
    }
    
    return results