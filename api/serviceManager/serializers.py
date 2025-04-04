from rest_framework import serializers

# Create a serializer for the request data
class RestartContainerSerializer(serializers.Serializer):
    container_id = serializers.CharField(required=True)
