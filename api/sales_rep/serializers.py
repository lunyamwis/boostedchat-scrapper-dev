from rest_framework import serializers

from .models import SalesRep


class SalesRepSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesRep
        fields = ["id", "user", "ig_username", "ig_password", "instagram",
                "app_version",
                "android_version",
                "android_release",
                "dpi",
                "resolution",
                "manufacturer",
                "device",
                "model",
                "cpu",
                "version_code",
                "status",
                "city",
                "country",
                "zip",
                "available",
                ]
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
            "instagram": {"required": False, "allow_null": True},
            "zip": {"required": False, "allow_null": True},
            "city": {"required": False, "allow_null": True},
            "country": {"required": False, "allow_null": True},
            "available": {"required": False, "allow_null": True},
        }


class AccountAssignmentSerializer(serializers.Serializer):
    REACTIONS = ((1, "Comment"), (2, "Direct Messaging"), (3, "Like"))

    reaction = serializers.ChoiceField(choices=REACTIONS)
