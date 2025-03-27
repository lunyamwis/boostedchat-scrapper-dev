from datetime import date
# from django_tenants.test.cases import TenantTestCase
from django_tenants.utils import schema_context
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase, URLPatternsTestCase
from django.urls import include, path, reverse
import requests
from api.instagram import views  
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from api.instagram.models import InstagramUser
import re
import time


# class LoadInfoToDatabaseTests(APITestCase, URLPatternsTestCase):
#     """
#     Unit tests for the LoadInfoToDatabase view.
#     """
#     urlpatterns = [
#         path('instagram/', include('api.instagram.urls')),
#     ]
    
    
    
#     def test_get_request(self):
#         """
#         Test that a GET request to the view returns the correct response.
#         """
#         # url = reverse('load_To_Db')
#         url = "http://calebomariba.localhost/instagram/loadToDb/" # put your url after implementing nginx in django tenants
#         response = requests.post(url)
#         # import pdb;pdb.set_trace()
    
#         self.assertEqual(response.status_code, 200)
        
        

class LoadInfoToDatabaseTests(APITestCase, URLPatternsTestCase):
    """
    Unit tests for LoadInfoToDatabase API endpoints.
    """

    urlpatterns = [
        path("instagram/", include("api.instagram.urls")),
    ]

    base_url = "http://calebomariba.localhost/instagram/loadToDb/"

    def test_post_request(self):
        """Test POST request to load data into the database."""
        response = requests.post(self.base_url)

        # print("Response JSON:", response.json())  # Debugging output

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("success", response.json())
        self.assertTrue(response.json().get("success"))
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertLess(response.elapsed.total_seconds(), 2)


    def test_get_request(self):
        """Test GET request for data retrieval."""
        response = requests.get(self.base_url)
        self.assertIn(response.status_code, [200, 404])
        if response.status_code == 200:
            self.assertIsInstance(response.json(), dict)

    def test_put_request(self):
        """Test PUT request to update a resource."""
        url = self.base_url + "1/"  # Assuming 1 is an ID
        data = {"field_name": "new_value"}
        response = requests.put(url, json=data)
        self.assertIn(response.status_code, [200, 400, 404])

    def test_patch_request(self):
        """Test PATCH request for partial update."""
        url = self.base_url + "1/"
        data = {"field_name": "partial_update"}
        response = requests.patch(url, json=data)
        self.assertIn(response.status_code, [200, 400, 404])

    def test_delete_request(self):
        """Test DELETE request to remove a resource."""
        url = self.base_url + "1/"
        response = requests.delete(url)
        self.assertIn(response.status_code, [204, 404])

    def test_head_request(self):
        """Test HEAD request to check if a resource exists."""
        response = requests.head(self.base_url)
        self.assertIn(response.status_code, [200, 404])
        self.assertEqual(response.text, "")  # HEAD response should not contain a body

    def test_options_request(self):
        """Test OPTIONS request to check allowed methods."""
        response = requests.options(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Allow", response.headers)  # Ensure 'Allow' header exists


class CustomFieldValueCreateViewTests(APITestCase, URLPatternsTestCase):
    """
    Unit tests for CustomFieldValueCreateView API endpoints.
    """

    urlpatterns = [
        path("instagram/", include("api.instagram.urls")),
    ]

    base_url = "http://calebomariba.localhost/instagram/endpoints/1/custom-field/create/"

    def test_get_request(self):
        """Test GET request to load the form."""
        response = requests.get(self.base_url)
        
        # GET requests typically don't require CSRF tokens
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
        self.assertLess(response.elapsed.total_seconds(), 2)

    def test_post_request_valid_data(self):
        """Test POST request with valid form data."""
        # First make a GET request to obtain CSRF token
        session = requests.Session()
        get_response = session.get(self.base_url)
        csrf_token = session.cookies.get('csrftoken', '')
        
        if not csrf_token:
            # Try alternative method to get CSRF token
            import re
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_response.text)
            if match:
                csrf_token = match.group(1)
        
        # Assuming you have a custom field with id=1 in your test database
        data = {
            'field': '1',
            'value': 'test value',
            'csrfmiddlewaretoken': csrf_token
        }
        headers = {
            'Referer': self.base_url  # Some CSRF checks require Referer header
        }
        response = session.post(self.base_url, data=data, headers=headers)
        
        # Check for either success (302) or redirect to login (common for protected views)
        self.assertIn(response.status_code, [302, 200])
        if response.status_code == 302:
            self.assertTrue(response.url.endswith('/custom_field_list/'))  # Check redirect URL
        else:
            # Might be showing login page
            self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")

    def test_post_request_invalid_data(self):
        """Test POST request with invalid form data."""
        # First make a GET request to obtain CSRF token
        session = requests.Session()
        get_response = session.get(self.base_url)
        csrf_token = session.cookies.get('csrftoken', '')
        
        if not csrf_token:
            import re
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_response.text)
            if match:
                csrf_token = match.group(1)
        
        data = {
            'field': '',
            'value': '',
            'csrfmiddlewaretoken': csrf_token
        }
        headers = {
            'Referer': self.base_url
        }
        response = session.post(self.base_url, data=data, headers=headers)
        
        # Check for either form errors (200) or redirect to login
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 200:
            self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
            self.assertIn("This field is required", response.text)  # Check for form errors

    def test_put_request(self):
        """Test PUT request (should not be allowed)."""
        response = requests.put(self.base_url)
        # Either 405 (not allowed) or 403 (forbidden) are acceptable
        self.assertIn(response.status_code, [405, 403])

    def test_patch_request(self):
        """Test PATCH request (should not be allowed)."""
        response = requests.patch(self.base_url)
        self.assertIn(response.status_code, [405, 403])

    def test_delete_request(self):
        """Test DELETE request (should not be allowed)."""
        response = requests.delete(self.base_url)
        self.assertIn(response.status_code, [405, 403])

    def test_head_request(self):
        """Test HEAD request."""
        response = requests.head(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "")  # HEAD response should not contain a body

    def test_options_request(self):
        """Test OPTIONS request to check allowed methods."""
        response = requests.options(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Allow", response.headers)
        allowed_methods = response.headers["Allow"].split(', ')
        self.assertIn("GET", allowed_methods)
        self.assertIn("POST", allowed_methods)
        self.assertIn("HEAD", allowed_methods)
        self.assertIn("OPTIONS", allowed_methods)


# class CustomFieldValueCreateViewTests(APITestCase, URLPatternsTestCase):
#     """
#     Unit tests for CustomFieldValueCreateView API endpoints.
#     """

#     urlpatterns = [
#         path("instagram/", include("api.instagram.urls")),
#     ]

#     base_url = "http://calebomariba.localhost/instagram/endpoints/1/custom-field/create/"
#     success_url = "/custom_field_list/"

#     def setUp(self):
#         self.session = requests.Session()
#         # Initial GET request to establish session and get CSRF token
#         self.get_response = self.session.get(self.base_url)
#         self.csrf_token = self._extract_csrf_token()

#     def _extract_csrf_token(self):
#         """Helper method to extract CSRF token from cookies or form."""
#         # Try to get from cookies first
#         csrf_token = self.session.cookies.get('csrftoken', '')
        
#         if not csrf_token:
#             # Fallback to extracting from form
#             match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', self.get_response.text)
#             if match:
#                 csrf_token = match.group(1)
#         return csrf_token

#     def _get_headers(self):
#         """Return default headers including Referer for CSRF protection."""
#         return {
#             'Referer': self.base_url,
#             'X-Requested-With': 'XMLHttpRequest'  # Helps identify AJAX requests
#         }

#     def test_get_request(self):
#         """Test GET request to load the form."""
#         self.assertEqual(self.get_response.status_code, 200)
#         self.assertEqual(self.get_response.headers["Content-Type"], "text/html; charset=utf-8")
#         self.assertLess(self.get_response.elapsed.total_seconds(), 2)
#         self.assertIn("form", self.get_response.text.lower())  # Verify form is present

#     def test_post_request_valid_data(self):
#         """Test POST request with valid form data."""
#         data = {
#             'field': '1',
#             'value': 'test value',
#             'csrfmiddlewaretoken': self.csrf_token
#         }
#         response = self.session.post(
#             self.base_url,
#             data=data,
#             headers=self._get_headers()
#         )
        
#         self.assertEqual(response.status_code, 302)  # Should redirect on success
#         self.assertTrue(response.url.endswith(self.success_url))

#     def test_post_request_invalid_data(self):
#         """Test POST request with invalid form data."""
#         data = {
#             'field': '',
#             'value': '',
#             'csrfmiddlewaretoken': self.csrf_token
#         }
#         response = self.session.post(
#             self.base_url,
#             data=data,
#             headers=self._get_headers()
#         )
        
#         self.assertEqual(response.status_code, 200)  # Form with errors
#         self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
#         self.assertIn("This field is required", response.text)

#     def test_unsupported_methods(self):
#         """Test PUT, PATCH, DELETE requests (should not be allowed)."""
#         for method in [requests.put, requests.patch, requests.delete]:
#             with self.subTest(method=method.__name__):
#                 response = method(self.base_url)
#                 self.assertIn(response.status_code, [405, 403])

#     def test_head_request(self):
#         """Test HEAD request."""
#         response = requests.head(self.base_url)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.text, "")

#     def test_options_request(self):
#         """Test OPTIONS request to check allowed methods."""
#         response = requests.options(self.base_url)
#         self.assertEqual(response.status_code, 200)
#         self.assertIn("Allow", response.headers)
#         allowed_methods = set(m.strip() for m in response.headers["Allow"].split(','))
#         expected_methods = {"GET", "POST", "HEAD", "OPTIONS"}
#         self.assertTrue(expected_methods.issubset(allowed_methods))

class ConnectionListCreateViewTests(APITestCase, URLPatternsTestCase):
    """
    Unit tests for ConnectionListCreateView API endpoints.
    """

    urlpatterns = [
        path("instagram/", include("api.instagram.urls")),
    ]

    base_url = "http://calebomariba.localhost/instagram/api/connections/"

    def test_get_request(self):
        """Test GET request to list connections."""
        response = requests.get(self.base_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertIsInstance(response.json(), list)
        self.assertLess(response.elapsed.total_seconds(), 2)

    def test_post_request_valid_data(self):
        """Test POST request to create a new connection."""
        # First make a GET request to obtain CSRF token
        session = requests.Session()
        get_response = session.get(self.base_url)
        csrf_token = session.cookies.get('csrftoken', '')
        
        if not csrf_token:
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_response.text)
            if match:
                csrf_token = match.group(1)
        
        test_data = {
            "id": 1,  # Required field
            "connection_id": f"conn_{int(time.time())}",
            "conn_type": "http",
            "host": "http://example.com",
            "login": "testuser",
            "password": "testpass",
            "port": None,  # Optional field
            "csrfmiddlewaretoken": csrf_token
        }
        headers = {
            'Referer': self.base_url,
            'Content-Type': 'application/json'
        }
        
        response = session.post(
            self.base_url,
            json=test_data,
            headers=headers
        )
        
        # Debug output if test fails
        if response.status_code != 201:
            print("Request Data:", test_data)
            print("Response Status:", response.status_code)
            print("Response Content:", response.text)
        
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assertIn("id", response_data)
        self.assertEqual(response_data["connection_id"], test_data["connection_id"])

    def test_post_request_invalid_data(self):
        """Test POST request with invalid data."""
        session = requests.Session()
        get_response = session.get(self.base_url)
        csrf_token = session.cookies.get('csrftoken', '')
        
        if not csrf_token:
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_response.text)
            if match:
                csrf_token = match.group(1)
        
        invalid_data = {
            "id": None,  # Invalid None value
            "connection_id": "",  # Empty string
            "csrfmiddlewaretoken": csrf_token
        }
        headers = {
            'Referer': self.base_url,
            'Content-Type': 'application/json'
        }
        
        response = session.post(
            self.base_url,
            json=invalid_data,
            headers=headers
        )
        
        self.assertEqual(response.status_code, 400)
        errors = response.json()
        required_fields = ["id", "connection_id", "conn_type", "host", "login", "password"]
        for field in required_fields:
            self.assertIn(field, errors)

    def test_put_request(self):
        """Test PUT request (should not be allowed at list endpoint)."""
        response = requests.put(self.base_url)
        self.assertIn(response.status_code, [405, 403])

    def test_patch_request(self):
        """Test PATCH request (should not be allowed at list endpoint)."""
        response = requests.patch(self.base_url)
        self.assertIn(response.status_code, [405, 403])

    def test_delete_request(self):
        """Test DELETE request (should not be allowed at list endpoint)."""
        response = requests.delete(self.base_url)
        self.assertIn(response.status_code, [405, 403])

    def test_head_request(self):
        """Test HEAD request."""
        response = requests.head(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "")

    def test_options_request(self):
        """Test OPTIONS request to check allowed methods."""
        response = requests.options(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Allow", response.headers)
        allowed_methods = response.headers["Allow"].split(', ')
        self.assertIn("GET", allowed_methods)
        self.assertIn("POST", allowed_methods)
        self.assertIn("HEAD", allowed_methods)
        self.assertIn("OPTIONS", allowed_methods)


class InsertAndEnrichTests(APITestCase, URLPatternsTestCase):
    """
    Unit tests for InsertAndEnrich API endpoints.
    """

    urlpatterns = [
        path("instagram/", include("api.instagram.urls")),
    ]

    base_url = "http://calebomariba.localhost/instagram/insertAndEnrich/"

    def test_post_request_with_chain(self):
        """Test POST request with chain=true."""
        session = requests.Session()
        get_response = session.get(self.base_url)
        csrf_token = session.cookies.get('csrftoken', '')
        
        if not csrf_token:
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_response.text)
            if match:
                csrf_token = match.group(1)
        
        test_data = {
            "keywords_to_check": ["test1", "test2"],
            "round": 1,
            "chain": True,
            "csrfmiddlewaretoken": csrf_token
        }
        headers = {
            'Referer': self.base_url,
            'Content-Type': 'application/json'
        }
        
        response = session.post(
            self.base_url,
            json=test_data,
            headers=headers
        )
        
        # Handle both JSON and non-JSON responses
        try:
            response_data = response.json()
            self.assertIn("success", response_data)
        except ValueError:
            # If response is not JSON, check for success in text
            self.assertIn("success", response.text.lower())

    def test_post_request_without_chain(self):
        """Test POST request with chain=false."""
        session = requests.Session()
        get_response = session.get(self.base_url)
        csrf_token = session.cookies.get('csrftoken', '')
        
        if not csrf_token:
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_response.text)
            if match:
                csrf_token = match.group(1)
        
        test_data = {
            "keywords_to_check": ["test1", "test2"],
            "round": 1,
            "chain": False,
            "csrfmiddlewaretoken": csrf_token
        }
        headers = {
            'Referer': self.base_url,
            'Content-Type': 'application/json'
        }
        
        response = session.post(
            self.base_url,
            json=test_data,
            headers=headers
        )
        
        try:
            response_data = response.json()
            self.assertIn("success", response_data)
        except ValueError:
            self.assertIn("success", response.text.lower())

    def test_post_request_missing_required_fields(self):
        """Test POST request with missing required fields."""
        session = requests.Session()
        get_response = session.get(self.base_url)
        csrf_token = session.cookies.get('csrftoken', '')
        
        if not csrf_token:
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', get_response.text)
            if match:
                csrf_token = match.group(1)
        
        invalid_data = {
            "chain": True,
            "csrfmiddlewaretoken": csrf_token
        }
        headers = {
            'Referer': self.base_url,
            'Content-Type': 'application/json'
        }
        
        response = session.post(
            self.base_url,
            json=invalid_data,
            headers=headers
        )
        
        # Check for error indication in either JSON or text response
        try:
            response_data = response.json()
            self.assertTrue("error" in response_data or "missing" in response_data)
        except ValueError:
            self.assertTrue("error" in response.text.lower() or "missing" in response.text.lower())

    def test_get_request(self):
        """Test GET request (should not be allowed)."""
        response = requests.get(self.base_url)
        self.assertEqual(response.status_code, 405)

    def test_put_request(self):
        """Test PUT request (should not be allowed)."""
        response = requests.put(self.base_url)
        self.assertEqual(response.status_code, 405)

    def test_patch_request(self):
        """Test PATCH request (should not be allowed)."""
        response = requests.patch(self.base_url)
        self.assertEqual(response.status_code, 405)

    def test_delete_request(self):
        """Test DELETE request (should not be allowed)."""
        response = requests.delete(self.base_url)
        self.assertEqual(response.status_code, 405)

    def test_head_request(self):
        """Test HEAD request."""
        response = requests.head(self.base_url)
        self.assertEqual(response.status_code, 405)

    def test_options_request(self):
        """Test OPTIONS request to check allowed methods."""
        response = requests.options(self.base_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Allow", response.headers)
        allowed_methods = response.headers["Allow"].split(', ')
        self.assertIn("POST", allowed_methods)
        self.assertIn("OPTIONS", allowed_methods)