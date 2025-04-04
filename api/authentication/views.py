import string
import random
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.twitter.views import TwitterOAuthAdapter
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.social_serializers import TwitterLoginSerializer
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view

from .models import User, AccountRequest
from .serializers import UserListSerializer, UserLoginSerializer, UserRegistrationSerializer, ActivateAccountSerializer, GetAccountRequestSerializer


def generate_password():
    """Generate random password."""
    all = string.ascii_uppercase + string.digits
    password = "".join(random.sample(all, 8))
    return password


class TwitterLogin(SocialLoginView):
    serializer_class = TwitterLoginSerializer
    adapter_class = TwitterOAuthAdapter


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLogin(SocialLoginView):  # if you want to use Implicit Grant, use this
    adapter_class = GoogleOAuth2Adapter


class AuthUserRegistrationView(APIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            serializer.save()
            status_code = status.HTTP_201_CREATED

            response = {
                "success": True,
                "statusCode": status_code,
                "message": "User successfully registered!",
                "user": serializer.data,
            }

            return Response(response, status=status_code)


class AuthUserLoginView(APIView):
    serializer_class = UserLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            status_code = status.HTTP_200_OK

            response = {
                "success": True,
                "statusCode": status_code,
                "message": "User logged in successfully",
                "access": serializer.data["access"],
                "refresh": serializer.data["refresh"],
                "authenticatedUser": {"email": serializer.data["email"], "role": serializer.data["role"]},
            }

            return Response(response, status=status_code)


class UserListView(APIView):
    serializer_class = UserListSerializer
    permission_classes = (AllowAny,)

    def get(self, request):
        users = User.objects.all()
        serializer = self.serializer_class(users, many=True)
        response = {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "message": "Successfully fetched users",
            "users": serializer.data,
        }
        return Response(response, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_account_requests(request):
    requests = AccountRequest.objects.select_related("user_id").order_by("requested_on")
    serializer = GetAccountRequestSerializer(
        requests, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def create_account_request(request):
    create_data = {**request.data, **{"status": "PENDING"}}

    user_serializer = UserRegistrationSerializer(data=create_data)
    if user_serializer.is_valid():
        user_serializer.save()

        account_request = AccountRequest()
        account_request.user_id = user_serializer.data["id"]
        account_request.save()

        return Response(user_serializer.data, status=status.HTTP_201_CREATED, )

    return Response({"errors": user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def approve_account_request(request, request_id):
    approved_by = request.data.get("approved_by")
    if approved_by is None:
        return Response({"message": "approved_by cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        account_request = AccountRequest.objects.get(id=request_id)
    except AccountRequest.DoesNotExist:
        return Response({"message": "Account request object does not exist"})

    try:
        user = User.objects.get(id=account_request.user_id)
    except User.DoesNotExist:
        return Response({"message": "User object does not exist"})

    account_request.approved_rejected_by = approved_by
    account_request.save()

    random_password = generate_password()
    user.set_password(random_password)
    user.status = "DORMANT"
    user.save()


@api_view(["POST"])
def reject_account_request(request, request_id):
    rejected_by = request.data.get("rejected_by")
    rejection_reason = request.data.get("rejection_reason")
    if rejected_by is None or rejection_reason is None:
        return Response({"message": "rejected_by and rejection_reason cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        account_request = AccountRequest.objects.get(id=request_id)
    except AccountRequest.DoesNotExist:
        return Response({"message": "Account request object does not exist"})

    try:
        user = User.objects.get(id=account_request.user_id)
    except User.DoesNotExist:
        return Response({"message": "User object does not exist"})

    account_request.approved_rejected_by = rejected_by
    account_request.save()

    user.status = "REJECTED"
    user.save()


@api_view(["POST"])
def activate_account(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"message": "User object does not exist"})

    if user.status != "DORMANT":
        return Response({"message": "The user account has already been activated"})

    serializer = ActivateAccountSerializer(data=request.data)

    if serializer.is_valid():
        if not user.check_password(serializer.validated_data["current_password"]):
            return Response({"message": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data["new_password"])
        user.status = "ACTIVE"
        user.save()

        return Response({"message": "Account activated successfully"})
    return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
