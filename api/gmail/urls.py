from django.urls import path
from . import views


urlpatterns = [
    path('auth/url/', views.GmailAuthURLView.as_view(), name='gmail_auth_url'),
    path('auth/callback/', views.GmailOAuthCallbackView.as_view(), name='gmail_oauth_callback'),
    path('accounts/', views.GmailAccountConnectView.as_view(), name='gmail_account_connect'),
    path('accounts/<str:account_id>/reconnect/', views.GmailAccountReconnectView.as_view(), name='gmail_account_reconnect'),
    path('accounts/<str:account_id>/emails/', views.GmailEmailsView.as_view(), name='gmail_emails'),
    path('accounts/<str:account_id>/emails/<str:email_id>/', views.GmailEmailView.as_view(), name='gmail_email'),
    path('accounts/<str:account_id>/emails/<str:email_id>/attachments/<str:attachment_id>/', views.GmailRetrieveAttachmentView.as_view(), name='gmail_retrieve_attachment'),
    path('accounts/<str:account_id>/folders/', views.GmailListFoldersView.as_view(), name='gmail_list_folders'),
    path('accounts/<str:account_id>/folders/<str:folder_id>/', views.GmailFolderView.as_view(), name='gmail_folder'),
    path('accounts/<str:account_id>/drafts/', views.GmailCreateDraftView.as_view(), name='gmail_create_draft'),
    path('accounts/<str:account_id>/webhooks/', views.GmailWebhooksView.as_view(), name='gmail_webhooks'),
    path('accounts/<str:account_id>/webhooks/<str:webhook_id>/', views.GmailWebhookView.as_view(), name='gmail_webhook'),
    
]