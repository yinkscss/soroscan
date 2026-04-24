"""
Custom GraphQL views with rate limiting and introspection control.
"""
import json

from django.conf import settings
from django.http import JsonResponse
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from strawberry.django.views import GraphQLView

from soroscan.throttles import IngestRateThrottle

_INTROSPECTION_FIELDS = {"__schema", "__type", "__typename"}


def _is_introspection_query(body: bytes) -> bool:
    """Return True if the request body contains a GraphQL introspection query."""
    try:
        data = json.loads(body)
        query = data.get("query", "") if isinstance(data, dict) else ""
    except (json.JSONDecodeError, AttributeError):
        return False
    return any(field in query for field in _INTROSPECTION_FIELDS)


class ThrottledGraphQLView(GraphQLView):
    """
    GraphQL view with rate limiting and optional introspection blocking.

    Set GRAPHQL_INTROSPECTION_ENABLED=False (default in production) to reject
    introspection queries with a 403 and a clear error message.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.anon_throttle = AnonRateThrottle()
        self.user_throttle = UserRateThrottle()
        self.ingest_throttle = IngestRateThrottle()

    def get_throttles(self, request):
        """Return list of throttle instances to check."""
        return [self.anon_throttle, self.user_throttle]

    def check_throttles(self, request):
        """Check if request should be throttled."""
        for throttle in self.get_throttles(request):
            if not throttle.allow_request(request, self):
                self.throttle_failure()

    def throttle_failure(self):
        """Handle throttle failure — raise 429."""
        from rest_framework.exceptions import Throttled

        raise Throttled(detail="Rate limit exceeded. Please try again later.")

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to add throttling and introspection checks."""
        self.check_throttles(request)

        introspection_enabled = getattr(settings, "GRAPHQL_INTROSPECTION_ENABLED", True)
        if not introspection_enabled and request.method == "POST":
            body = request.body
            if _is_introspection_query(body):
                return JsonResponse(
                    {
                        "errors": [
                            {
                                "message": (
                                    "GraphQL introspection is disabled in production. "
                                    "Set GRAPHQL_INTROSPECTION_ENABLED=True to enable it."
                                )
                            }
                        ]
                    },
                    status=403,
                )

        return super().dispatch(request, *args, **kwargs)
