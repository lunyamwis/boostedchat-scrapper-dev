from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, FilePath, HttpUrl, ValidationError, validator


def validate_external_url(cls, v):
    if v is None or (v.startswith("http") and "://" in v) or isinstance(v, str):
        return v
    raise ValidationError("external_url must been URL or string")


class Resource(BaseModel):
    pk: Union[str, int]
    video_url: Optional[HttpUrl] = None  # for Video and IGTV
    thumbnail_url: Optional[HttpUrl] = None
    media_type: Optional[int] = None


class User(BaseModel):
    pk: Union[str, int]
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_private: Optional[bool] = False
    profile_pic_url: Optional[HttpUrl] = None
    profile_pic_url_hd: Optional[HttpUrl] = None
    is_verified: Optional[bool] = False
    media_count: Optional[int] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    biography: Optional[str] = ""
    external_url: Optional[str]
    account_type: Optional[int]
    is_business: Optional[bool] = False

    public_email: Optional[str] = None
    contact_phone_number: Optional[str] = None
    public_phone_country_code: Optional[str] = None
    public_phone_number: Optional[str] = None
    business_contact_method: Optional[str] = None
    business_category_name: Optional[str] = None
    category_name: Optional[str] = None
    category: Optional[str] = None

    address_street: Optional[str] = None
    city_id: Optional[str] = None
    city_name: Optional[str] = None
    latitude: Optional[float] = 0.0
    longitude: Optional[float] = 0.0
    zip: Optional[str] = None
    instagram_location_id: Optional[str] = None
    interop_messaging_user_fbid: Optional[str] = None

    _external_url = validator("external_url", allow_reuse=True)(validate_external_url)


class Account(BaseModel):
    pk: Union[str, int]
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_private: Optional[bool] = False
    profile_pic_url: Optional[HttpUrl] = None
    is_verified: Optional[bool] = False
    biography: Optional[str] = ""
    external_url: Optional[str]
    is_business: Optional[bool] = False
    birthday: Optional[str]
    phone_number: Optional[str]
    gender: Optional[int]
    email: Optional[str]

    _external_url = validator("external_url", allow_reuse=True)(validate_external_url)



class UserShort(BaseModel):
    pk: Union[str, int]  # This field is required and cannot be None
    username: Optional[str] = None  # Optional field with default as None
    full_name: Optional[str] = None  # Optional field with default as None
    profile_pic_url: Optional[HttpUrl] = None  # Optional field with default as None
    profile_pic_url_hd: Optional[HttpUrl] = None  # Optional field with default as None
    is_private: Optional[bool] = None  # Optional field with default as None
    stories: List = []  # Default to an empty list

class Usertag(BaseModel):
    user: UserShort
    x: float
    y: float


class Location(BaseModel):
    pk: Optional[int]
    name: Optional[str] = None
    phone: Optional[str] = ""
    website: Optional[str] = ""
    category: Optional[str] = ""
    hours: Optional[dict] = {}  # opening hours
    address: Optional[str] = ""
    city: Optional[str] = ""
    zip: Optional[str] = ""
    lng: Optional[float]
    lat: Optional[float]
    external_id: Optional[int]
    external_id_source: Optional[str]
    # address_json: Optional[dict] = {}
    # profile_pic_url: Optional[HttpUrl]
    # directory: Optional[dict] = {}


class Media(BaseModel):
    pk: Union[str, int]
    id: Optional[str] = None
    code: Optional[str] = None
    taken_at: datetime
    media_type: Optional[int] = None
    image_versions2: Optional[dict] = {}
    product_type: Optional[str] = ""  # igtv or feed
    thumbnail_url: Optional[HttpUrl] = None
    location: Optional[Location] = None
    user: UserShort
    comment_count: Optional[int] = 0
    comments_disabled: Optional[bool] = False
    commenting_disabled_for_viewer: Optional[bool] = False
    like_count: Optional[int] = None
    play_count: Optional[int] = None
    has_liked: Optional[bool] = False
    caption_text: Optional[str] = None
    accessibility_caption: Optional[str] = None
    usertags: List[Usertag]
    sponsor_tags: List[UserShort]
    video_url: Optional[HttpUrl] = None   # for Video and IGTV
    view_count: Optional[int] = 0  # for Video and IGTV
    video_duration: Optional[float] = 0.0  # for Video and IGTV
    title: Optional[str] = ""
    resources: List[Resource] = []
    clips_metadata: dict = {}


class MediaXma(BaseModel):
    #media_type: Optional[int] = None
    video_url: Optional[HttpUrl] = None  # for Video and IGTV
    title: Optional[str] = ""
    preview_url: Optional[HttpUrl]
    preview_url_mime_type: Optional[str]
    header_icon_url: Optional[HttpUrl]
    header_icon_width: Optional[int]
    header_icon_height: Optional[int]
    header_title_text: Optional[str]
    preview_media_fbid: Optional[str]


class MediaOembed(BaseModel):
    title: Optional[str] = None
    author_name: Optional[str] = None
    author_url: Optional[str] = None
    author_id: Optional[str] = None
    media_id: Optional[str] = None
    provider_name: Optional[str] = None
    provider_url: Optional[HttpUrl] = None
    type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    html: Optional[str] = None
    thumbnail_url: Optional[HttpUrl] = None
    thumbnail_width: Optional[int] = None
    thumbnail_height: Optional[int] = None
    can_view: Optional[bool] = False


class Collection(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    media_count: Optional[int] = None


class Comment(BaseModel):
    pk: Union[str, int]
    text: Optional[str] = None
    user: UserShort
    created_at_utc: datetime
    content_type: Optional[str] = None
    status: Optional[str] = None
    has_liked: Optional[bool]
    like_count: Optional[int]


class Hashtag(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    media_count: Optional[int]
    profile_pic_url: Optional[HttpUrl]


class StoryMention(BaseModel):
    user: UserShort
    x: Optional[float]
    y: Optional[float]
    width: Optional[float]
    height: Optional[float]


class StoryMedia(BaseModel):
    # Instagram does not return the feed_media object when requesting story,
    # so you will have to make an additional request to get media and this is overhead:
    # media: Media
    x: float = 0.5
    y: float = 0.4997396
    z: float = 0
    width: float = 0.8
    height: float = 0.60572916
    rotation: float = 0.0
    is_pinned: Optional[bool]
    is_hidden: Optional[bool]
    is_sticker: Optional[bool]
    is_fb_sticker: Optional[bool]
    media_pk: Optional[int] = None
    user_id: Optional[int]
    product_type: Optional[str]
    media_code: Optional[str]


class StoryHashtag(BaseModel):
    hashtag: Hashtag
    x: Optional[float]
    y: Optional[float]
    width: Optional[float]
    height: Optional[float]


class StoryLocation(BaseModel):
    location: Location
    x: Optional[float]
    y: Optional[float]
    width: Optional[float]
    height: Optional[float]


class StoryStickerLink(BaseModel):
    url: Optional[HttpUrl] = None
    link_title: Optional[str]
    link_type: Optional[str]
    display_url: Optional[str]


class StorySticker(BaseModel):
    id: Optional[str]
    type: Optional[str] = "gif"
    x: float
    y: float
    z: Optional[int] = 1000005
    width: float
    height: float
    rotation: Optional[float] = 0.0
    story_link: Optional[StoryStickerLink]
    extra: Optional[dict] = {}


class StoryBuild(BaseModel):
    mentions: List[StoryMention]
    path: FilePath
    paths: List[FilePath] = []
    stickers: List[StorySticker] = []


class StoryLink(BaseModel):
    webUri: Optional[HttpUrl] = None
    x: float = 0.5126011
    y: float = 0.5168225
    z: float = 0.0
    width: float = 0.50998676
    height: float = 0.25875
    rotation: float = 0.0


class Story(BaseModel):
    pk: Union[str, int]
    id: Optional[str] = None
    code: Optional[str] = None
    taken_at: datetime
    media_type: Optional[int] = None
    product_type: Optional[str] = ""
    thumbnail_url: Optional[HttpUrl]
    user: UserShort
    video_url: Optional[HttpUrl] = None  # for Video and IGTV
    video_duration: Optional[float] = 0.0  # for Video and IGTV
    sponsor_tags: List[UserShort]
    mentions: List[StoryMention]
    links: List[StoryLink]
    hashtags: List[StoryHashtag]
    locations: List[StoryLocation]
    stickers: List[StorySticker]
    medias: List[StoryMedia] = []


class DirectMedia(BaseModel):
    id: Optional[str] = None
    media_type: Optional[int] = None
    user: Optional[UserShort]
    thumbnail_url: Optional[HttpUrl]
    video_url: Optional[HttpUrl] = None
    audio_url: Optional[HttpUrl]


class ReplyMessage(BaseModel):
    id: Optional[str] = None
    user_id: Optional[int]
    timestamp: datetime
    item_type: Optional[str]
    is_sent_by_viewer: Optional[bool]
    is_shh_mode: Optional[bool]
    text: Optional[str]
    link: Optional[dict]
    animated_media: Optional[dict]
    media: Optional[DirectMedia]
    visual_media: Optional[dict]
    media_share: Optional[Media]
    reel_share: Optional[dict]
    story_share: Optional[dict]
    felix_share: Optional[dict]
    xma_share: Optional[MediaXma]
    clip: Optional[Media]
    placeholder: Optional[dict]


class DirectMessage(BaseModel):
    id: Optional[str] = None  # e.g. 28597946203914980615241927545176064
    user_id: Optional[int]
    thread_id: Optional[int]  # e.g. 340282366841710300949128531777654287254
    timestamp: datetime
    item_type: Optional[str]
    is_sent_by_viewer: Optional[bool]
    is_shh_mode: Optional[bool]
    reactions: Optional[dict]
    text: Optional[str]
    reply: Optional[ReplyMessage]
    link: Optional[dict]
    animated_media: Optional[dict]
    media: Optional[DirectMedia]
    visual_media: Optional[dict]
    media_share: Optional[Media]
    reel_share: Optional[dict]
    story_share: Optional[dict]
    felix_share: Optional[dict]
    xma_share: Optional[MediaXma]
    clip: Optional[Media]
    placeholder: Optional[dict]


class DirectResponse(BaseModel):
    unseen_count: Optional[int]
    unseen_count_ts: Optional[int]
    status: Optional[str]


class DirectShortThread(BaseModel):
    id: Optional[str] = None
    users: List[UserShort]
    named: Optional[bool] = False
    thread_title: Optional[str] = None
    pending: Optional[bool] = False
    thread_type: Optional[str] = None
    viewer_id: Optional[str] = None
    is_group: Optional[bool] = False


class DirectThread(BaseModel):
    pk: Union[str, int]  # thread_v2_id, e.g. 17898572618026348
    id: Optional[str] = None  # thread_id, e.g. 340282366841510300949128268610842297468
    messages: List[DirectMessage]
    users: List[UserShort]
    inviter: Optional[UserShort]
    left_users: List[UserShort] = []
    admin_user_ids: list
    last_activity_at: datetime
    muted: Optional[bool] = False
    is_pin: Optional[bool]
    named: Optional[bool] = False
    canonical: Optional[bool] = False
    pending: Optional[bool] = False
    archived: Optional[bool] = False
    thread_type: Optional[str] = None
    thread_title: Optional[str] = None
    folder: Optional[int] = None
    vc_muted: Optional[bool] = False
    is_group: Optional[bool] = False
    mentions_muted: Optional[bool] = False
    approval_required_for_new_members: Optional[bool] = False
    input_mode: Optional[int] = None
    business_thread_folder: Optional[int] = None
    read_state: Optional[int] = None
    is_close_friend_thread: Optional[bool] = False
    assigned_admin_id: Optional[int] = None
    shh_mode_enabled: Optional[bool] = False
    last_seen_at: dict

    def is_seen(self, user_id: Optional[str] = None):
        """Have I seen this thread?
        :param user_id: You account user_id
        """
        user_id = str(user_id)
        own_timestamp = int(self.last_seen_at[user_id]["timestamp"])
        timestamps = [
            (int(v["timestamp"]) - own_timestamp) > 0
            for k, v in self.last_seen_at.items()
            if k != user_id
        ]
        return not any(timestamps)


class Relationship(BaseModel):
    blocking: Optional[bool] = False
    followed_by: Optional[bool] = False
    following: Optional[bool] = False
    incoming_request: Optional[bool] = False
    is_bestie: Optional[bool] = False
    is_blocking_reel: Optional[bool] = False
    is_muting_reel: Optional[bool] = False
    is_private: Optional[bool] = False
    is_restricted: Optional[bool] = False
    muting: Optional[bool] = False
    outgoing_request: Optional[bool] = False
    status: Optional[str] = None


class Highlight(BaseModel):
    pk: Union[str, int]  # 17895485401104052
    id: Optional[str] = None  # highlight:17895485401104052
    latest_reel_media: Optional[int] = None
    cover_media: dict
    user: UserShort
    title: Optional[str] = None
    created_at: datetime
    is_pinned_highlight: Optional[bool] = False
    media_count: Optional[int] = None
    media_ids: List[int] = []
    items: List[Story] = []


class Share(BaseModel):
    pk: Union[str, int]
    type: Optional[str] = None


class Track(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    display_artist: Optional[str] = None
    audio_cluster_id: Optional[int] = None
    artist_id: Optional[int]
    cover_artwork_uri: Optional[HttpUrl]
    cover_artwork_thumbnail_uri: Optional[HttpUrl]
    progressive_download_url: Optional[HttpUrl]
    fast_start_progressive_download_url: Optional[HttpUrl]
    reactive_audio_download_url: Optional[HttpUrl]
    highlight_start_times_in_ms: List[int]
    is_explicit: Optional[bool] = False
    dash_manifest: Optional[str] = None
    uri: Optional[HttpUrl]
    has_lyrics: Optional[bool] = False
    audio_asset_id: Optional[int] = None
    duration_in_ms: Optional[int] = None
    dark_message: Optional[str]
    allows_saving: Optional[bool] = False
    territory_validity_periods: dict


class NoteResponse(BaseModel):
    id: Optional[str] = None
    text: Optional[str] = None
    user_id: Optional[int] = None
    user: UserShort
    audience: Optional[int] = None
    created_at: datetime
    expires_at: datetime
    is_emoji_only: Optional[bool] = False
    has_translation: Optional[bool] = False
    note_style: Optional[int] = None
    status: Optional[str] = None


class NoteRequest(BaseModel):
    text: Optional[str] = None
    uuid: Optional[str] = None
