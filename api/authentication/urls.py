from django.urls import path,include,re_path
from rest_framework_simplejwt import views as jwt_views

from dj_rest_auth.views import (
    LogoutView, PasswordChangeView, PasswordResetConfirmView,
    PasswordResetView, UserDetailsView,
)
from dj_rest_auth.registration.views import (
    SocialAccountListView, SocialAccountDisconnectView,
    VerifyEmailView, ResendEmailVerificationView

)
from django.views.generic import TemplateView


from .views import (
    AuthUserRegistrationView,
    AuthUserLoginView,
    UserListView,
    FacebookLogin,
    TwitterLogin,
    GoogleLogin,
    get_account_requests,
    create_account_request,
    approve_account_request,
    reject_account_request,
    activate_account
)
 

urlpatterns = [
    path('', UserListView.as_view(), name='users'),
    path('token/obtain/', jwt_views.TokenObtainPairView.as_view(), name='token_create'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('register', AuthUserRegistrationView.as_view(), name='register'),
    path('login', AuthUserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='rest_logout'),
    path('user/', UserDetailsView.as_view(), name='rest_user_details'),
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('auth/facebook/connect/', FacebookLogin.as_view(), name='fb_connect'),
    path('auth/twitter/connect/', TwitterLogin.as_view(), name='twitter_connect'),
    path(
        'socialaccounts/',
        SocialAccountListView.as_view(),
        name='social_account_list'
    ),
    path(
        'socialaccounts/<int:pk>/disconnect/',
        SocialAccountDisconnectView.as_view(),
        name='social_account_disconnect'
    ),
    path('verify-email/', VerifyEmailView.as_view(), name='rest_verify_email'),
    path('resend-email/', ResendEmailVerificationView.as_view(), name="rest_resend_email"),
    re_path(
        r'^account-confirm-email/(?P<key>[-:\w]+)/$', TemplateView.as_view(),
        name='account_confirm_email',
    ),
    path(
        'account-email-verification-sent/', TemplateView.as_view(),
        name='account_email_verification_sent',
    ),
    path('password/change/', PasswordChangeView.as_view(), name='rest_password_change'),
    path('password/reset/', PasswordResetView.as_view(), name='rest_password_reset'),
    path('password/reset/confirm/<str:uidb64>/<str:token>', PasswordResetConfirmView.as_view(),
            name='password_reset_confirm'),
    path('account-request/all/', get_account_requests, name="get_account_request"),
    path('account-request/create/', create_account_request, name="create_account_request"),
    path('account-request/approve/<request_id>/', approve_account_request, name="approve_account_request"),
    path('account-request/reject/<request_id>/', reject_account_request, name="reject_account_request"),
    path('account-request/activate/<user_id>/', activate_account, name="activate_account")
]
