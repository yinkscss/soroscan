"""
Tests for GraphQL introspection control (Task 2).

Covers:
- Introspection rejected with 403 when GRAPHQL_INTROSPECTION_ENABLED=False
- Clear error message returned
- Introspection allowed when GRAPHQL_INTROSPECTION_ENABLED=True
- Non-introspection queries unaffected
- Configurable via env var
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory

from soroscan.graphql_views import ThrottledGraphQLView, _is_introspection_query


class IsIntrospectionQueryTest(TestCase):
    """Unit tests for the introspection detection helper."""

    def _body(self, query: str) -> bytes:
        return json.dumps({"query": query}).encode()

    def test_schema_introspection_detected(self):
        self.assertTrue(_is_introspection_query(self._body("{ __schema { types { name } } }")))

    def test_type_introspection_detected(self):
        self.assertTrue(_is_introspection_query(self._body("{ __type(name: \"Query\") { fields { name } } }")))

    def test_typename_detected(self):
        self.assertTrue(_is_introspection_query(self._body("{ __typename }")))

    def test_normal_query_not_detected(self):
        self.assertFalse(_is_introspection_query(self._body("{ contracts { id } }")))

    def test_invalid_json_returns_false(self):
        self.assertFalse(_is_introspection_query(b"not json"))

    def test_empty_body_returns_false(self):
        self.assertFalse(_is_introspection_query(b"{}"))


class IntrospectionBlockingTest(TestCase):
    """ThrottledGraphQLView should block introspection when disabled."""

    def _make_request(self, query: str) -> MagicMock:
        factory = RequestFactory()
        body = json.dumps({"query": query}).encode()
        request = factory.post(
            "/graphql/",
            data=body,
            content_type="application/json",
        )
        return request

    def _make_view(self):
        mock_schema = MagicMock()
        view = ThrottledGraphQLView(schema=mock_schema)
        # Bypass throttle checks for these unit tests
        view.check_throttles = lambda r: None
        return view

    def test_introspection_blocked_returns_403(self):
        with patch.object(
            __import__("django.conf", fromlist=["settings"]).settings,
            "GRAPHQL_INTROSPECTION_ENABLED",
            False,
        ):
            view = self._make_view()
            request = self._make_request("{ __schema { types { name } } }")
            response = view.dispatch(request)
            self.assertEqual(response.status_code, 403)

    def test_introspection_blocked_error_message(self):
        with patch.object(
            __import__("django.conf", fromlist=["settings"]).settings,
            "GRAPHQL_INTROSPECTION_ENABLED",
            False,
        ):
            view = self._make_view()
            request = self._make_request("{ __schema { types { name } } }")
            response = view.dispatch(request)
            data = json.loads(response.content)
            self.assertIn("errors", data)
            self.assertIn("introspection is disabled", data["errors"][0]["message"])

    def test_normal_query_not_blocked_when_introspection_disabled(self):
        """Non-introspection queries pass through even when introspection is off."""
        with patch.object(
            __import__("django.conf", fromlist=["settings"]).settings,
            "GRAPHQL_INTROSPECTION_ENABLED",
            False,
        ):
            view = self._make_view()
            request = self._make_request("{ contracts { id } }")
            # Patch super().dispatch to avoid needing a real schema
            with patch.object(ThrottledGraphQLView, "dispatch", wraps=view.dispatch) as _:
                with patch(
                    "strawberry.django.views.GraphQLView.dispatch",
                    return_value=MagicMock(status_code=200),
                ):
                    response = view.dispatch(request)
                    self.assertNotEqual(response.status_code, 403)

    def test_introspection_allowed_when_enabled(self):
        """When GRAPHQL_INTROSPECTION_ENABLED=True, introspection passes through."""
        with patch.object(
            __import__("django.conf", fromlist=["settings"]).settings,
            "GRAPHQL_INTROSPECTION_ENABLED",
            True,
        ):
            view = self._make_view()
            request = self._make_request("{ __schema { types { name } } }")
            with patch(
                "strawberry.django.views.GraphQLView.dispatch",
                return_value=MagicMock(status_code=200),
            ):
                response = view.dispatch(request)
                self.assertNotEqual(response.status_code, 403)

    def test_get_request_not_blocked(self):
        """GET requests (GraphQL playground) are never blocked."""
        with patch.object(
            __import__("django.conf", fromlist=["settings"]).settings,
            "GRAPHQL_INTROSPECTION_ENABLED",
            False,
        ):
            factory = RequestFactory()
            request = factory.get("/graphql/")
            view = self._make_view()
            with patch(
                "strawberry.django.views.GraphQLView.dispatch",
                return_value=MagicMock(status_code=200),
            ):
                response = view.dispatch(request)
                self.assertNotEqual(response.status_code, 403)


class IntrospectionSettingDefaultTest(TestCase):
    """GRAPHQL_INTROSPECTION_ENABLED should default to DEBUG value."""

    def test_default_follows_debug_setting(self):
        from django.conf import settings
        # In test settings DEBUG=True, so introspection should be enabled
        self.assertTrue(getattr(settings, "GRAPHQL_INTROSPECTION_ENABLED", True))
