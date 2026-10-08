"""Core views for Amanus Learn AI API."""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Health check endpoint for API and load balancers.
    Returns status: ok to confirm service availability.
    """

    authentication_classes = ()
    permission_classes = ()

    @extend_schema(
        summary="Service Health Check",
        description="Returns system health status for monitoring and container orchestration.",
        responses={
            200: OpenApiResponse(
                description="Service is healthy",
                response={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "ok"},
                    },
                },
            )
        },
        tags=["Monitoring"],
    )
    def get(self, request, *args, **kwargs):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
