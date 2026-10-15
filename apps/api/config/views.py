"""Core views for Amanus Learn AI API."""

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


def metrics_view(request):
    """Prometheus scrape endpoint.

    Plain Django response (not part of the OpenAPI contract). Served on the
    internal Docker network only: nginx never routes /metrics to the API.
    Metrics carry no user, organization or document identifiers.
    """
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


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
