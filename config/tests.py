from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "config-api-tests",
    }
}


@override_settings(CACHES=TEST_CACHES)
class SchemaAPITests(APITestCase):
    def test_schema_endpoint_returns_openapi_document(self):
        response = self.client.get("/api/schema/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_docs_endpoint_is_available(self):
        response = self.client.get("/api/docs/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
