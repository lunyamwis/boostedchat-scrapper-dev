from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework.routers import DefaultRouter
from django.urls import path,include

from .views import (AccountViewSet,
    CommentViewSet,
    ExperimentAssigneeViewSet,
    LikeViewSet,
    DMViewset,
    HashTagViewSet,
    MessageViewSet,
    PhotoViewSet,
    ReelViewSet,
    StoryViewSet,
    VideoViewSet,
    OutSourcedViewSet,
    ExperimentViewSet,
    ExperimentFieldDefinitionViewSet,
    ExperimentStatusViewSet,
    ExperimentFieldValueViewSet
)

router = DefaultRouter()
router.register(r"outsourced",OutSourcedViewSet,basename="outsourced")
router.register(r"account", AccountViewSet, basename="account")
router.register(r"comment", CommentViewSet, basename="comment")
router.register(r"like",LikeViewSet,basename="like")
router.register(r"hashtag", HashTagViewSet, basename="hashtag")
router.register(r"photo", PhotoViewSet, basename="photo")
router.register(r"video", VideoViewSet, basename="video")
router.register(r"reel", ReelViewSet, basename="reel")
router.register(r"story", StoryViewSet, basename="story")
router.register(r"dm", DMViewset, basename="dm")
router.register(r"message", MessageViewSet, basename="message")
router.register(r'instagramLead', views.InstagramLeadViewSet)
router.register(r'scores', views.ScoreViewSet)
router.register(r'qualification_algorithms', views.QualificationAlgorithmViewSet)
router.register(r'schedulers', views.SchedulerViewSet)
router.register(r'lead_sources', views.LeadSourceViewSet)
router.register(r'media',views.MediaViewSet)
router.register(r'experiments', ExperimentViewSet, basename='experiment')
router.register(r'experiment_assignees', ExperimentAssigneeViewSet, basename='experiment_assignee')
router.register(r'experiment_status', ExperimentStatusViewSet, basename='experiment_status')
router.register(r'experiment_fields', ExperimentFieldDefinitionViewSet, basename='experiment_field_definition')
router.register(r'experiment_field_values', ExperimentFieldValueViewSet, basename='experiment_field_value')


urlpatterns = [
    path('', include(router.urls)),
    path(
        'dflow/<str:thread_id>/generate-response/',
        DMViewset.as_view({'post': 'generate_response'}),
        name='generate_response',
    ),
    path(
        'dflow/<str:thread_id>/generate-response/v2/',
        DMViewset.as_view({'post': 'generate_response_v2'}),
        name='generate_response_v2',
    ),
    path(
        'celery-task-status/<str:task_id>/',
        DMViewset.as_view({'get': 'celery_task_status'}),
        name='celery_task_status',
    ),
    path(
        'sendFirstResponses/',
        DMViewset.as_view({'post': 'get_qualified_threads_and_respond'}),
        name='get_qualified_threads_and_respond',
    ),
    path(
        'getOutreachAccounts/',
        DMViewset.as_view({'post': 'get_accounts_to_be_reached_out_to_today'}),
        name='get_accounts_to_be_reached_out_to_today',
    ),
    path(
        'checkAccountExists/',
        DMViewset.as_view({'post': 'check_account_exists'}),
        name='check_account_exists',
    ),
    path(
        'checkThreadExists/',
        DMViewset.as_view({'post': 'check_thread_exists'}),
        name='check_thread_exists',
    ),
    path(
        'fallback/<str:username>/assign-operator/',
        DMViewset.as_view({'post': 'assign_operator'}),
        name='assign_operator',
    ),
    path(
        'webhook/',
        DMViewset.as_view({'post': 'webhook'}),
        name='webhook',
    ),
    path(
        'dm/messages-by-ig-thread/<str:ig_thread_id>/',
        DMViewset.as_view({'get': 'messages_by_ig_thread_id'}),
        name='messages_by_ig_thread_id',
    ),
    path(
        'dm/thread-by-ig-thread/<str:ig_thread_id>/',
        DMViewset.as_view({'get': 'thread_by_ig_thread_id'}),
        name='thread_by_ig_thread_id',
    ),
    path(
        'has-client-responded/',
        DMViewset.as_view({'get': 'has_client_responded'}),
        name='has_client_responded',
    ),
    path(
        'send-follow-up-responses/',
        DMViewset.as_view({'post': 'generate_followup_response'}),
        name='generate_followup_response',
    ),
    path(
        'send-follow-up-v2/',
        DMViewset.as_view({'post': 'generate_followup_response_v2'}),
        name='generate_followup_response_v2',
    ),
    path(
        'account/account-by-ig-thread/<str:ig_thread_id>/',
        AccountViewSet.as_view({'get': 'account_by_ig_thread_id'}),
        name='account_by_ig_thread_id',
    ),
    path(
        'account/retrieve-salesrep/<str:username>/',
        AccountViewSet.as_view({'get': 'retrieve_salesrep'}),
        name='retrieve_salesrep',
    ),
    path(
        'account/create-account-manually/',
        AccountViewSet.as_view({'post': 'create-account-manually'}),
        name='create-account-manually',
    ),
    path(
        'account/weekly-reporting/',
        AccountViewSet.as_view({'get': 'weekly-reporting'}),
        name='weekly-reporting',
    ),
    path(
        'experiments/<str:pk>/experiment_fields/',
        ExperimentViewSet.as_view({'get': 'get_field_definitions'}),
        name='get_field_definitions',
    ),
    path('comment-likers-chunk-gql/', views.HikerCommentLikersChunkGql.as_view(), name='comment-likers-chunk-gql'),
    path('comments-chunk-gql/', views.HikerCommentsChunkGql.as_view(), name='comments-chunk-gql'),
    path('comments-threaded-chunk-gql/', views.HikerCommentsThreadedChunkGql.as_view(), name='comments-threaded-chunk-gql'),
    path('fbsearch-accounts-v2/', views.HikerFbsearchAccountsV2.as_view(), name='fbsearch-accounts-v2'),
    path('fbsearch-places-v1/', views.HikerFbsearchPlacesV1.as_view(), name='fbsearch-places-v1'),
    path('fbsearch-places-v2/', views.HikerFbsearchPlacesV2.as_view(), name='fbsearch-places-v2'),
    path('fbsearch-reels-v2/', views.HikerFbsearchReelsV2.as_view(), name='fbsearch-reels-v2'),
    path('fbsearch-topsearch-hashtags-v1/', views.HikerFbsearchTopsearchHashtagsV1.as_view(), name='fbsearch-topsearch-hashtags-v1'),
    path('fbsearch-topsearch-v1/', views.HikerFbsearchTopsearchV1.as_view(), name='fbsearch-topsearch-v1'),
    path('fbsearch-topsearch-v2/', views.HikerFbsearchTopsearchV2.as_view(), name='fbsearch-topsearch-v2'),
    path('hashtag-by-name-v1/', views.HikerHashtagByNameV1.as_view(), name='hashtag-by-name-v1'),
    path('hashtag-by-name-v2/', views.HikerHashtagByNameV2.as_view(), name='hashtag-by-name-v2'),
    path('hashtag-medias-clips-chunk-v1/', views.HikerHashtagMediasClipsChunkV1.as_view(), name='hashtag-medias-clips-chunk-v1'),
    path('hashtag-medias-clips-v1/', views.HikerHashtagMediasClipsV1.as_view(), name='hashtag-medias-clips-v1'),
    path('hashtag-medias-clips-v2/', views.HikerHashtagMediasClipsV2.as_view(), name='hashtag-medias-clips-v2'),
    path('hashtag-medias-recent-v2/', views.HikerHashtagMediasRecentV2.as_view(), name='hashtag-medias-recent-v2'),
    path('hashtag-medias-top-chunk-v1/', views.HikerHashtagMediasTopChunkV1.as_view(), name='hashtag-medias-top-chunk-v1'),
    path('hashtag-medias-top-recent-chunk-v1/', views.HikerHashtagMediasTopRecentChunkV1.as_view(), name='hashtag-medias-top-recent-chunk-v1'),
    path('hashtag-medias-top-v1/', views.HikerHashtagMediasTopV1.as_view(), name='hashtag-medias-top-v1'),
    path('hashtag-medias-top-v2/', views.HikerHashtagMediasTopV2.as_view(), name='hashtag-medias-top-v2'),
    path('highlight-by-id-v2/', views.HikerHighlightByIdV2.as_view(), name='highlight-by-id-v2'),
    path('highlight-by-url-v1/', views.HikerHighlightByUrlV1.as_view(), name='highlight-by-url-v1'),
    path('location-by-id-v1/', views.HikerLocationByIdV1.as_view(), name='location-by-id-v1'),
    path('location-guides-v1/', views.HikerLocationGuidesV1.as_view(), name='location-guides-v1'),
    path('location-medias-recent-chunk-v1/', views.HikerLocationMediasRecentChunkV1.as_view(), name='location-medias-recent-chunk-v1'),
    path('location-medias-recent-v1/', views.HikerLocationMediasRecentV1.as_view(), name='location-medias-recent-v1'),
    path('location-medias-top-chunk-v1/', views.HikerLocationMediasTopChunkV1.as_view(), name='location-medias-top-chunk-v1'),
    path('location-medias-top-v1/', views.HikerLocationMediasTopV1.as_view(), name='location-medias-top-v1'),
    path('location-search-v1/', views.HikerLocationSearchV1.as_view(), name='location-search-v1'),
    path('media-by-code-v1/', views.HikerMediaByCodeV1.as_view(), name='media-by-code-v1'),
    path('media-by-id-v1/', views.HikerMediaByIdV1.as_view(), name='media-by-id-v1'),
    path('media-by-url-v1/', views.HikerMediaByUrlV1.as_view(), name='media-by-url-v1'),
    path('media-code-from-pk-v1/', views.HikerMediaCodeFromPkV1.as_view(), name='media-code-from-pk-v1'),
    path('media-comment-offensive-v2/', views.HikerMediaCommentOffensiveV2.as_view(), name='media-comment-offensive-v2'),
    path('media-comments/', views.HikerMediaComments.as_view(), name='media-comments'),
    path('media-comments-chunk-v1/', views.HikerMediaCommentsChunkV1.as_view(), name='media-comments-chunk-v1'),
    path('media-comments-v2/', views.HikerMediaCommentsV2.as_view(), name='media-comments-v2'),
    path('media-info-by-code-v2/', views.HikerMediaInfoByCodeV2.as_view(), name='media-info-by-code-v2'),
    path('media-info-by-id-v2/', views.HikerMediaInfoByIdV2.as_view(), name='media-info-by-id-v2'),
    path('media-info-by-url-v2/', views.HikerMediaInfoByUrlV2.as_view(), name='media-info-by-url-v2'),
    path('media-insight-v1/', views.HikerMediaInsightV1.as_view(), name='media-insight-v1'),
    path('media-likers-gql/', views.HikerMediaLikersGql.as_view(), name='media-likers-gql'),
    path('media-likers-v1/', views.HikerMediaLikersV1.as_view(), name='media-likers-v1'),
    path('media-likers-v2/', views.HikerMediaLikersV2.as_view(), name='media-likers-v2'),
    path('media-oembed-v1/', views.HikerMediaOembedV1.as_view(), name='media-oembed-v1'),
    path('media-pk-from-code-v1/', views.HikerMediaPkFromCodeV1.as_view(), name='media-pk-from-code-v1'),
    path('media-pk-from-url-v1/', views.HikerMediaPkFromUrlV1.as_view(), name='media-pk-from-url-v1'),
    path('media-template-v2/', views.HikerMediaTemplateV2.as_view(), name='media-template-v2'),
    path('media-user-v1/', views.HikerMediaUserV1.as_view(), name='media-user-v1'),
    path('save-media/', views.HikerSaveMedia.as_view(), name='save-media'),
    path('search-accounts-v2/', views.HikerSearchAccountsV2.as_view(), name='search-accounts-v2'),
    path('search-hashtags-v1/', views.HikerSearchHashtagsV1.as_view(), name='search-hashtags-v1'),
    path('search-hashtags-v2/', views.HikerSearchHashtagsV2.as_view(), name='search-hashtags-v2'),
    path('search-music-v1/', views.HikerSearchMusicV1.as_view(), name='search-music-v1'),
    path('search-music-v2/', views.HikerSearchMusicV2.as_view(), name='search-music-v2'),
    path('search-places-v2/', views.HikerSearchPlacesV2.as_view(), name='search-places-v2'),
    path('search-reels-v2/', views.HikerSearchReelsV2.as_view(), name='search-reels-v2'),
    path('search-topsearch-v2/', views.HikerSearchTopsearchV2.as_view(), name='search-topsearch-v2'),
    path('search-users-v1/', views.HikerSearchUsersV1.as_view(), name='search-users-v1'),
    path('share-by-code-v1/', views.HikerShareByCodeV1.as_view(), name='share-by-code-v1'),
    path('share-by-url-v1/', views.HikerShareByUrlV1.as_view(), name='share-by-url-v1'),
    path('share-reel-by-url-v1/', views.HikerShareReelByUrlV1.as_view(), name='share-reel-by-url-v1'),
    path('story-by-id-v1/', views.HikerStoryByIdV1.as_view(), name='story-by-id-v1'),
    path('story-by-url-v1/', views.HikerStoryByUrlV1.as_view(), name='story-by-url-v1'),
    path('story-by-url-v2/', views.HikerStoryByUrlV2.as_view(), name='story-by-url-v2'),
    path('story-download-by-story-url-v1/', views.HikerStoryDownloadByStoryUrlV1.as_view(), name='story-download-by-story-url-v1'),
    path('story-download-by-url-v1/', views.HikerStoryDownloadByUrlV1.as_view(), name='story-download-by-url-v1'),
    path('story-download-v1/', views.HikerStoryDownloadV1.as_view(), name='story-download-v1'),
    path('track-by-canonical-id-v2/', views.HikerTrackByCanonicalIdV2.as_view(), name='track-by-canonical-id-v2'),
    path('track-by-id-v2/', views.HikerTrackByIdV2.as_view(), name='track-by-id-v2'),
    path('track-stream-by-id-v2/', views.HikerTrackStreamByIdV2.as_view(), name='track-stream-by-id-v2'),
    path('user-a2/', views.HikerUserA2.as_view(), name='user-a2'),
    path('user-about-v1/', views.HikerUserAboutV1.as_view(), name='user-about-v1'),
    path('user-by-id-v1/', views.HikerUserByIdV1.as_view(), name='user-by-id-v1'),
    path('user-by-id-v2/', views.HikerUserByIdV2.as_view(), name='user-by-id-v2'),
    path('user-by-url-v1/', views.HikerUserByUrlV1.as_view(), name='user-by-url-v1'),
    path('user-by-username-v1/', views.HikerUserByUsernameV1.as_view(), name='user-by-username-v1'),
    path('user-by-username-v2/', views.HikerUserByUsernameV2.as_view(), name='user-by-username-v2'),
    path('user-clips-chunk-v1/', views.HikerUserClipsChunkV1.as_view(), name='user-clips-chunk-v1'),
    path('user-clips-v2/', views.HikerUserClipsV2.as_view(), name='user-clips-v2'),
    path('user-explore-businesses-by-id-v2/', views.HikerUserExploreBusinessesByIdV2.as_view(), name='user-explore-businesses-by-id-v2'),
    path('user-followers-chunk-gql/', views.HikerUserFollowersChunkGql.as_view(), name='user-followers-chunk-gql'),
    path('user-followers-chunk-v1/', views.HikerUserFollowersChunkV1.as_view(), name='user-followers-chunk-v1'),
    path('user-followers-v2/', views.HikerUserFollowersV2.as_view(), name='user-followers-v2'),
    path('user-following/', views.HikerUserFollowing.as_view(), name='user-following'),
    path('user-following-chunk-gql/', views.HikerUserFollowingChunkGql.as_view(), name='user-following-chunk-gql'),
    path('user-following-chunk-v1/', views.HikerUserFollowingChunkV1.as_view(), name='user-following-chunk-v1'),
    path('user-following-v2/', views.HikerUserFollowingV2.as_view(), name='user-following-v2'),
    path('user-highlights/', views.HikerUserHighlights.as_view(), name='user-highlights'),
    path('user-highlights-by-username-v1/', views.HikerUserHighlightsByUsernameV1.as_view(), name='user-highlights-by-username-v1'),
    path('user-highlights-by-username-v2/', views.HikerUserHighlightsByUsernameV2.as_view(), name='user-highlights-by-username-v2'),
    path('user-highlights-v1/', views.HikerUserHighlightsV1.as_view(), name='user-highlights-v1'),
    path('user-highlights-v2/', views.HikerUserHighlightsV2.as_view(), name='user-highlights-v2'),
    path('user-medias/', views.HikerUserMedias.as_view(), name='user-medias'),
    path('user-medias-chunk-v1/', views.HikerUserMediasChunkV1.as_view(), name='user-medias-chunk-v1'),
    path('user-medias-pinned-v1/', views.HikerUserMediasPinnedV1.as_view(), name='user-medias-pinned-v1'),
    path('user-medias-v2/', views.HikerUserMediasV2.as_view(), name='user-medias-v2'),
    path('user-related-profiles-gql/', views.HikerUserRelatedProfilesGql.as_view(), name='user-related-profiles-gql'),
    path('user-search-followers-v1/', views.HikerUserSearchFollowersV1.as_view(), name='user-search-followers-v1'),
    path('user-search-following-v1/', views.HikerUserSearchFollowingV1.as_view(), name='user-search-following-v1'),
    path('user-stories-by-username-v1/', views.HikerUserStoriesByUsernameV1.as_view(), name='user-stories-by-username-v1'),
    path('user-stories-by-username-v2/', views.HikerUserStoriesByUsernameV2.as_view(), name='user-stories-by-username-v2'),
    path('user-stories-v1/', views.HikerUserStoriesV1.as_view(), name='user-stories-v1'),
    path('user-stories-v2/', views.HikerUserStoriesV2.as_view(), name='user-stories-v2'),
    path('user-tag-medias-chunk-v1/', views.HikerUserTagMediasChunkV1.as_view(), name='user-tag-medias-chunk-v1'),
    path('user-tag-medias-v2/', views.HikerUserTagMediasV2.as_view(), name='user-tag-medias-v2'),
    path('user-web-profile-info-v1/', views.HikerUserWebProfileInfoV1.as_view(), name='user-web-profile-info-v1'),
    path('userstream-by-id-v2/', views.HikerUserstreamByIdV2.as_view(), name='userstream-by-id-v2'),
    path('userstream-by-username-v2/', views.HikerUserstreamByUsernameV2.as_view(), name='userstream-by-username-v2')
]

