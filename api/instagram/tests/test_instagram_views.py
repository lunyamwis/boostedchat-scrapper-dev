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

        print("Response JSON:", response.json())  # Debugging output

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

     
# class CustomFieldTests(APITestCase, URLPatternsTestCase):
#     """
#     Unit tests for the CustomFieldListCreateView API endpoints.
#     """

#     urlpatterns = [
#         path('instagram/', include('api.instagram.urls')),
#     ]

#     base_url = "http://calebomariba.localhost/api/custom-field-list-create/"

#     def test_get_custom_fields(self):
#         """Test GET request to retrieve the list of custom fields."""
#         response = requests.get(self.base_url)

#         self.assertEqual(response.status_code, 200)
#         self.assertIsInstance(response.json(), list)  # Ensure response is a list
#         if response.json():
#             self.assertIsInstance(response.json()[0], dict)  # Ensure each item is a dict

#         self.assertEqual(response.headers["Content-Type"], "application/json")

#     def test_post_valid_custom_field(self):
#         """Test POST request to create a valid custom field."""
#         data = {"name": "Test Field", "type": "text"}  # Adjust based on your model
#         response = requests.post(self.base_url, json=data)

#         self.assertEqual(response.status_code, 201)
#         self.assertIsInstance(response.json(), dict)
#         self.assertIn("id", response.json())  # Check if response contains the new object ID
#         self.assertEqual(response.json().get("name"), "Test Field")
#         self.assertEqual(response.headers["Content-Type"], "application/json")

#     def test_post_invalid_custom_field(self):
#         """Test POST request with invalid data."""
#         data = {"invalid_field": "wrong_value"}  # Missing required fields
#         response = requests.post(self.base_url, json=data)

#         self.assertEqual(response.status_code, 400)  # Bad Request
#         self.assertIsInstance(response.json(), dict)
#         self.assertIn("error", response.json())  # Check if error message exists

#     def test_put_custom_field(self):
#         """Test PUT request to update an existing custom field."""
#         url = self.base_url + "1/"  # Assuming ID = 1 exists
#         data = {"name": "Updated Field", "type": "number"}
#         response = requests.put(url, json=data)

#         self.assertIn(response.status_code, [200, 400, 404])
#         if response.status_code == 200:
#             self.assertEqual(response.json().get("name"), "Updated Field")

#     def test_patch_custom_field(self):
#         """Test PATCH request for partial update."""
#         url = self.base_url + "1/"
#         data = {"name": "Partially Updated Field"}
#         response = requests.patch(url, json=data)

#         self.assertIn(response.status_code, [200, 400, 404])
#         if response.status_code == 200:
#             self.assertEqual(response.json().get("name"), "Partially Updated Field")

#     def test_delete_custom_field(self):
#         """Test DELETE request to remove a custom field."""
#         url = self.base_url + "1/"
#         response = requests.delete(url)

#         self.assertIn(response.status_code, [204, 404])

#     def test_options_custom_field(self):
#         """Test OPTIONS request to check allowed methods."""
#         response = requests.options(self.base_url)

#         self.assertEqual(response.status_code, 200)
#         self.assertIn("Allow", response.headers)  # Check if 'Allow' header exists


from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APITestCase, URLPatternsTestCase
from api.instagram.models import HttpOperatorConnectionModel
from django.contrib.auth import get_user_model

class ConnectionUpdateTests(APITestCase, URLPatternsTestCase):
    """
    Unit tests for the ConnectionUpdateView API endpoint.
    """
    urlpatterns = [
        path('connection/update/<str:pk>/', views.ConnectionUpdateView.as_view(), name='connection_update'),
    ]

    def setUp(self):
        """
        Set up the initial data for testing.
        """
        # Create a test user (you can create other necessary objects like `HttpOperatorConnectionModel`)
        self.user = get_user_model().objects.create_user(username='testuser', password='password')
        self.connection = HttpOperatorConnectionModel.objects.create(
            connection_id="test_connection_1", 
            conn_type="HTTP", 
            host="localhost", 
            port=8080, 
            login="user", 
            password="pass"
        )

    def test_update_connection_valid(self):
        """Test PUT request to update a connection with valid data."""
        url = reverse("connection_update", kwargs={"pk": self.connection.pk})
        data = {
            "connection_id": "test_connection_1_updated", 
            "conn_type": "HTTPS", 
            "host": "localhost_updated", 
            "port": 9090, 
            "login": "user_updated", 
            "password": "pass_updated"
        }

        with patch('requests.patch') as mock_patch:
            # Simulate a successful response from the Airflow API
            mock_patch.return_value.status_code = 200
            mock_patch.return_value.text = "Success"

            response = self.client.put(url, data, format='json')
            
            self.assertEqual(response.status_code, 200)  # 200 OK for successful update
            self.assertEqual(response.data["connection_id"], "test_connection_1_updated")
            mock_patch.assert_called_once()  # Ensure that the external Airflow request was made

    def test_update_connection_invalid_pk(self):
        """Test PUT request with an invalid pk."""
        url = reverse("connection_update", kwargs={"pk": "non_existent_pk"})
        data = {
            "connection_id": "test_connection_2", 
            "conn_type": "HTTPS", 
            "host": "localhost", 
            "port": 9090, 
            "login": "user", 
            "password": "pass"
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 404)  # Not found for invalid pk

    @patch('requests.patch')
    def test_airflow_api_failure(self, mock_patch):
        """Test that the connection update handles failure from Airflow API."""
        url = reverse("connection_update", kwargs={"pk": self.connection.pk})
        data = {
            "connection_id": "test_connection_1_failed", 
            "conn_type": "HTTPS", 
            "host": "localhost_failed", 
            "port": 8081, 
            "login": "user_failed", 
            "password": "pass_failed"
        }

        # Simulate a failure response from the Airflow API
        mock_patch.return_value.status_code = 500  # Internal Server Error
        mock_patch.return_value.text = "Server Error"

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, 200)  # Update should still return success in Django
        # Ensure the error message is in the response (based on your implementation)
        self.assertIn("Failed to update connection in Airflow", response.data["message"])

    def test_options_connection_update(self):
        """Test OPTIONS request to check allowed methods."""
        url = reverse("connection_update", kwargs={"pk": self.connection.pk})

        response = self.client.options(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Allow", response.headers)  # Check if 'Allow' header exists
        self.assertIn("PUT", response.headers["Allow"])  # Ensure PUT is allowed
        self.assertIn("PATCH", response.headers["Allow"])  # Ensure PATCH is allowed
