from django.shortcuts import render
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Room, RoomMember
from .serializers import RoomCreateSerializer

class RoomCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = RoomCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data.get("name", "")

        room = Room.create_with_unique_code(
            owner=request.user,
            name=name
        )

        RoomMember.objects.create(
            room = room,
            user = request.user,
            role = RoomMember.Role.OWNER
        )

        return Response(
            {
                "id": room.id,
                "name": room.name,
                "code": room.code,
            },
            status = status.HTTP_201_CREATED
        )