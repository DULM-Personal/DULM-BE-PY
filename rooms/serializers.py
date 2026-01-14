from rest_framework import serializers

class RoomCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=60, required=False, allow_blank=True)