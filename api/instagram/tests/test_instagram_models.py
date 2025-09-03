import os
from django.test import TestCase
from api.instagram.models import (
                InstagramUser, 
                AirflowCreds, 
                HttpOperatorConnectionModel,
                DagModel,
                WorkflowModel,
                CustomField,
                CustomFieldValue,
                Endpoint,
                PostgresOperatorModel,
                SimpleHttpOperatorModel,
                Media
                )
from django_tenants.utils import schema_context
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User 
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.contrib.postgres.fields import ArrayField


class InstagramUserTest(TestCase):
    @classmethod
    @schema_context(os.getenv('SCHEMA_NAME'))
    def setUpTestData(cls):
        InstagramUser.objects.create(username='test_user')

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_instagram_user_creation(self):
        user = InstagramUser.objects.get(username='test_user')
        self.assertEqual(user.username, 'test_user')

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_instagram_user_str_representation(self):
        user = InstagramUser.objects.get(username='test_user')
        self.assertEqual(str(user), 'test_user')

class AirflowCredsTest(TestCase):
    @classmethod
    @schema_context(os.getenv('SCHEMA_NAME'))
    def setUpTestData(cls):
        """Create an AirflowCreds instance for testing."""
        AirflowCreds.objects.create(
            username="airflow_user",
            password="securepassword123",
            schema_name="test_schema",
            airflow_base_url="http://localhost:8080"
        )

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_airflow_creds_creation(self):
        """Test if AirflowCreds instance is created successfully."""
        creds = AirflowCreds.objects.get(username="airflow_user")
        self.assertEqual(creds.username, "airflow_user")
        self.assertEqual(creds.schema_name, "test_schema")
        self.assertEqual(creds.airflow_base_url, "http://localhost:8080")
    
    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_airflow_creds_str_representation(self):
        """Test the __str__ method returns the schema_name."""
        creds = AirflowCreds.objects.get(username="airflow_user")
        self.assertEqual(str(creds), "test_schema")

class HttpOperatorConnectionModelTest(TestCase):
    @classmethod
    @schema_context(os.getenv('SCHEMA_NAME'))
    def setUpTestData(cls):
        """Create an HttpOperatorConnectionModel instance for testing."""
        HttpOperatorConnectionModel.objects.create(
            connection_id="http_conn_1",
            conn_type="http",
            host="http://example.com",
            port=8080,
            login="admin",
            password="securepassword"
        )

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_http_operator_connection_creation(self):
        """Test if HttpOperatorConnectionModel instance is created successfully."""
        connection = HttpOperatorConnectionModel.objects.get(connection_id="http_conn_1")
        self.assertEqual(connection.connection_id, "http_conn_1")
        self.assertEqual(connection.conn_type, "http")
        self.assertEqual(connection.host, "http://example.com")
        self.assertEqual(connection.port, 8080)
        self.assertEqual(connection.login, "admin")

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_http_operator_connection_str_representation(self):
        """Test the __str__ method returns the connection_id."""
        connection = HttpOperatorConnectionModel.objects.get(connection_id="http_conn_1")
        self.assertEqual(str(connection), "http_conn_1")

class DagModelTest(TestCase):
    @classmethod
    @schema_context(os.getenv('SCHEMA_NAME'))
    def setUpTestData(cls):
        """Create related models and a DagModel instance for testing."""
        connection = HttpOperatorConnectionModel.objects.create(
            connection_id="http_conn_1",
            conn_type="http",
            host="http://example.com",
            port=8080,
            login="admin",
            password="securepassword"
        )

        workflow = WorkflowModel.objects.create(
            name="Test Workflow"
        )

        DagModel.objects.create(
            dag_id="test_dag",
            description="Test DAG Description",
            schedule="0 0 * * *",
            schedule_interval="daily",
            timetable="test_timetable",
            start_date=now(),
            end_date=None,
            full_filepath="/path/to/dag.py",
            template_searchpath="/templates",
            user_defined_macros={"macro1": "value1"},
            user_defined_filters={"filter1": "value1"},
            default_args={"owner": "admin"},
            concurrency=5,
            max_active_tasks=3,
            max_active_runs=2,
            dagrun_timeout=None,
            default_view="graph",
            orientation="LR",
            catchup=True,
            doc_md="Test DAG Documentation",
            params={"param1": "value1"},
            access_control={"role": ["read", "write"]},
            is_paused_upon_creation=False,
            jinja_environment_kwargs={"trim_blocks": True},
            render_template_as_native_obj=True,
            tags=["tag1", "tag2"],
            owner_links={"admin": "https://example.com"},
            auto_register=True,
            fail_stop=False,
            trigger_url="http://trigger.url",
            connection=connection,
            trigger_url_expected_key="status",
            trigger_url_expected_value="success",
            workflow=workflow
        )

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_dag_model_creation(self):
        """Test if DagModel instance is created successfully."""
        dag = DagModel.objects.get(dag_id="test_dag")
        self.assertEqual(dag.dag_id, "test_dag")
        self.assertEqual(dag.description, "Test DAG Description")
        self.assertEqual(dag.schedule, "0 0 * * *")
        self.assertEqual(dag.schedule_interval, "daily")
        self.assertEqual(dag.timetable, "test_timetable")
        self.assertTrue(dag.catchup)
        self.assertEqual(dag.default_view, "graph")
        self.assertEqual(dag.trigger_url, "http://trigger.url")
        self.assertEqual(dag.trigger_url_expected_key, "status")
        self.assertEqual(dag.trigger_url_expected_value, "success")
        self.assertEqual(dag.connection.connection_id, "http_conn_1")
        self.assertEqual(dag.workflow.name, "Test Workflow")
        self.assertIn("tag1", dag.tags)
        self.assertIn("tag2", dag.tags)

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_dag_model_str_representation(self):
        """Test the __str__ method returns the dag_id."""
        dag = DagModel.objects.get(dag_id="test_dag")
        self.assertEqual(str(dag), "test_dag")

class CustomFieldTest(TestCase):
    @classmethod
    @schema_context(os.getenv('SCHEMA_NAME'))
    def setUpTestData(cls):
        """Create a test CustomField object."""
        cls.custom_field = CustomField.objects.create(name="Test Field", data_type="text")

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_custom_field_creation(self):
        """Test if the CustomField instance is created properly."""
        field = CustomField.objects.get(name="Test Field")
        self.assertEqual(field.name, "Test Field")
        self.assertEqual(field.data_type, "text")

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_custom_field_str_representation(self):
        """Test the __str__ method of CustomField."""
        field = CustomField.objects.get(name="Test Field")
        self.assertEqual(str(field), "Test Field")

    # @schema_context(os.getenv('SCHEMA_NAME'))
    # def test_custom_field_data_type_choices(self):
    #     """Test that only valid choices are accepted for data_type."""
    #     valid_types = ["text", "number", "date", "boolean", "json"]
    #     for data_type in valid_types:
    #         field = CustomField.objects.create(name=f"Field {data_type}", data_type=data_type)
    #         self.assertEqual(field.data_type, data_type)

    #     # Invalid data_type should raise an error
    #     with self.assertRaises(Exception):
    #         CustomField.objects.create(name="Invalid Field", data_type="invalid_choice")


    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_custom_field_data_type_choices(self):
        """Test that only valid choices are accepted for data_type."""
        valid_types = ["text", "number", "date", "boolean", "json"]
        for data_type in valid_types:
            field = CustomField.objects.create(name=f"Field {data_type}", data_type=data_type)
            self.assertEqual(field.data_type, data_type)

        # Invalid data_type should raise ValidationError
        with self.assertRaises(ValidationError):
            CustomField.objects.create(name="Invalid Field", data_type="invalid_choice")
    
    # @schema_context(os.getenv('SCHEMA_NAME'))
    # def test_custom_field_data_type_choices(self):
    #     """Test that only valid choices are accepted for data_type."""
    #     valid_types = ["text", "number", "date", "boolean", "json"]
    #     for data_type in valid_types:
    #         field = CustomField(name=f"Field {data_type}", data_type=data_type)
    #         field.full_clean()  # This ensures Django runs `choices` validation.
    #         field.save()
    #         self.assertEqual(field.data_type, data_type)

    #     # Invalid data_type should raise ValidationError
    #     with self.assertRaises(ValidationError):
    #         field = CustomField(name="Invalid Field", data_type="invalid_choice")
    #         field.full_clean()  # Raises ValidationError before saving
    #         field.save()



SCHEMA_NAME = os.getenv('SCHEMA_NAME', 'public') 

class CustomFieldValueTest(TestCase):

    @schema_context(SCHEMA_NAME)
    def test_custom_field_value_creation(self):
        """Test that a CustomFieldValue instance can be created correctly."""
        field = CustomField.objects.create(id="field-1", name="Test Field", data_type="json")
        content_type = ContentType.objects.get_for_model(User)
        obj_id = "12345"

        custom_value = CustomFieldValue.objects.create(
            id="value-1",
            field=field,
            content_type=content_type,
            object_id=obj_id,
            value={"key": "value"}
        )

        self.assertEqual(custom_value.field, field)
        self.assertEqual(custom_value.content_type, content_type)
        self.assertEqual(custom_value.object_id, obj_id)
        self.assertEqual(custom_value.value, {"key": "value"})

    @schema_context(SCHEMA_NAME)
    def test_custom_field_value_str_representation(self):
        """Test the string representation of CustomFieldValue."""
        field = CustomField.objects.create(id="field-2", name="Age", data_type="number")
        content_type = ContentType.objects.get_for_model(User)
        custom_value = CustomFieldValue.objects.create(
            id="value-2", field=field, value=25,
            content_type=content_type, 
            object_id="12345",
        )
        self.assertEqual(str(custom_value), "Age: 25")

    @schema_context(SCHEMA_NAME)
    def test_invalid_custom_field_value(self):
        """Test that an invalid CustomFieldValue raises a ValidationError."""
        field = CustomField.objects.create(id="field-3", name="Invalid Field", data_type="text")

        invalid_value = CustomFieldValue(id="value-3", field=field, value={"unexpected": "dict"})

        with self.assertRaises(ValidationError):
            invalid_value.full_clean()  # This triggers Django's validation

SCHEMA_NAME = os.getenv('SCHEMA_NAME', 'public')  # Default schema if not set

class EndpointModelTest(TestCase):

    @schema_context(SCHEMA_NAME)
    def setUp(self):
        """Set up the initial data for tests."""
        self.endpoint = Endpoint.objects.create(
            base_url="https://api.example.com", 
            url="/data", 
            method="GET"
        )
        # Create a CustomField to be linked to the Endpoint model
        self.field = CustomField.objects.create(id="field-1", name="Test Field", data_type="json")
        self.content_type = ContentType.objects.get_for_model(Endpoint)
        self.custom_field_value = CustomFieldValue.objects.create(
            id="value-1", 
            field=self.field, 
            content_type=self.content_type, 
            object_id=self.endpoint.id,
            value={"key": "value"}
        )

    @schema_context(SCHEMA_NAME)
    def test_str_representation(self):
        """Test the string representation of Endpoint."""
        self.assertEqual(str(self.endpoint), "/data")

    @schema_context(SCHEMA_NAME)
    def test_custom_fields_property(self):
        """Test that the custom_fields property returns the correct related objects."""
        custom_fields = self.endpoint.custom_fields
        self.assertEqual(custom_fields.count(), 1)
        self.assertEqual(custom_fields.first().value, {"key": "value"})
        
    @schema_context(SCHEMA_NAME)
    def test_endpoint_integrity_error(self):
        """Test that an IntegrityError or ValidationError is raised if required fields are missing."""
        endpoint = Endpoint(method='POST')  # No `url` provided, should raise ValidationError or IntegrityError based on the validation logic

        with self.assertRaises(ValidationError):
            endpoint.full_clean()  # This triggers the validation and should raise a ValidationError if `url` is empty

    @schema_context(SCHEMA_NAME)
    def test_invalid_method_field(self):
        """Test that the method field can only have valid choices."""
        with self.assertRaises(ValidationError):
            endpoint = Endpoint(base_url="https://api.example.com", url="/invalid_method", method="PUT")
            endpoint.full_clean()  # This will trigger validation

    @schema_context(SCHEMA_NAME)
    def test_missing_url(self):
        """Test that missing URL raises a ValidationError."""
        endpoint = Endpoint(method='POST')  # No `url` provided
        with self.assertRaises(ValidationError):
            endpoint.full_clean()  # This will validate and raise an error if `url` is empty


    @schema_context(SCHEMA_NAME)
    def test_missing_method(self):
        """Test that missing method defaults to 'GET'."""
        endpoint = Endpoint.objects.create(base_url="https://api.example.com", url="/missing_method")
        self.assertEqual(endpoint.method, "GET")


SCHEMA_NAME = os.getenv('SCHEMA_NAME', 'public')  

class PostgresOperatorModelTest(TestCase):

    @schema_context(SCHEMA_NAME)
    def test_postgres_operator_model_creation(self):
        """Test the creation of a PostgresOperatorModel instance."""
        # Set up related models first
        connection = HttpOperatorConnectionModel.objects.create(
            connection_id='conn-1',
            host='localhost',
            port=5432
        )
        dag = DagModel.objects.create(
            dag_id='dag-1',
            schedule_interval='@daily'
        )
        
        # Create the PostgresOperatorModel instance
        postgres_operator = PostgresOperatorModel.objects.create(
            task_id="task-1",
            connection=connection,
            sql="SELECT * FROM my_table;",
            autocommit=True,
            parameters={"param1": "value1"},
            dag=dag
        )
        
        # Assert that the instance was created correctly
        self.assertEqual(postgres_operator.task_id, "task-1")
        self.assertEqual(postgres_operator.connection, connection)
        self.assertEqual(postgres_operator.sql, "SELECT * FROM my_table;")
        self.assertTrue(postgres_operator.autocommit)
        self.assertEqual(postgres_operator.parameters, {"param1": "value1"})
        self.assertEqual(postgres_operator.dag, dag)

    @schema_context(SCHEMA_NAME)
    def test_postgres_operator_model_missing_task_id(self):
        """Test that a PostgresOperatorModel without a task_id raises a ValidationError."""
        connection = HttpOperatorConnectionModel.objects.create(
            connection_id='conn-1',
            host='localhost',
            port=5432
        )
        dag = DagModel.objects.create(
            dag_id='dag-1',
            schedule_interval='@daily'
        )
        
        # Create the PostgresOperatorModel instance without task_id (should raise ValidationError)
        postgres_operator = PostgresOperatorModel(
            connection=connection,
            sql="SELECT * FROM my_table;",
            autocommit=True,
            parameters={"param1": "value1"},
            dag=dag
        )
        
        with self.assertRaises(ValidationError):
            postgres_operator.full_clean()  # This will raise a ValidationError because task_id is required

    @schema_context(SCHEMA_NAME)
    def test_postgres_operator_model_missing_sql(self):
        """Test that a PostgresOperatorModel without an SQL query raises a ValidationError."""
        connection = HttpOperatorConnectionModel.objects.create(
            connection_id='conn-1',
            host='localhost',
            port=5432
        )
        dag = DagModel.objects.create(
            dag_id='dag-1',
            schedule_interval='@daily'
        )
        
        # Create the PostgresOperatorModel instance without SQL (should raise ValidationError)
        postgres_operator = PostgresOperatorModel(
            task_id="task-2",
            connection=connection,
            autocommit=True,
            parameters={"param1": "value1"},
            dag=dag
        )
        
        with self.assertRaises(ValidationError):
            postgres_operator.full_clean()  # This will raise a ValidationError because sql is required

    @schema_context(SCHEMA_NAME)
    def test_postgres_operator_model_default_values(self):
        """Test the default values of the PostgresOperatorModel fields."""
        connection = HttpOperatorConnectionModel.objects.create(
            connection_id='conn-1',
            host='localhost',
            port=5432
        )
        dag = DagModel.objects.create(
            dag_id='dag-1',
            schedule_interval='@daily'
        )
        
        # Create the PostgresOperatorModel instance with default values for autocommit and parameters
        postgres_operator = PostgresOperatorModel.objects.create(
            task_id="task-3",
            connection=connection,
            sql="SELECT * FROM another_table;",
            dag=dag
        )
        
        # Assert default values
        self.assertFalse(postgres_operator.autocommit)  
        self.assertIsNone(postgres_operator.parameters) 

    @schema_context(SCHEMA_NAME)
    def test_postgres_operator_model_str_method(self):
        """Test the string representation of the PostgresOperatorModel."""
        connection = HttpOperatorConnectionModel.objects.create(
            connection_id='conn-1',
            host='localhost',
            port=5432
        )
        dag = DagModel.objects.create(
            dag_id='dag-1',
            schedule_interval='@daily'
        )
        
        # Create the PostgresOperatorModel instance
        postgres_operator = PostgresOperatorModel.objects.create(
            task_id="task-4",
            connection=connection,
            sql="SELECT * FROM users;",
            autocommit=True,
            parameters={"param1": "value1"},
            dag=dag
        )
        
        # Test the string representation
        self.assertEqual(str(postgres_operator), "task-4")


SCHEMA_NAME = os.getenv('SCHEMA_NAME', 'public')  # Default schema

class SimpleHttpOperatorModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up test data before running tests."""
        list_of_dag_ids=["test_dag_1", "test_dag_2"]
        with schema_context(SCHEMA_NAME):  
            cls.connection = HttpOperatorConnectionModel.objects.create(
                connection_id="test_conn_123",
                conn_type="http",  # Correct field
                host="https://api.example.com",
                port=443,
                login="user",
                password="password",
            )

            cls.endpoint = Endpoint.objects.create(url="https://api.example.com/test")

            cls.dag = DagModel.objects.create(
                dag_id="test_dag",
                description="Test DAG",
                schedule="0 12 * * *",
                schedule_interval="daily"
            )

            cls.http_operator = SimpleHttpOperatorModel.objects.create(
                task_id="test_task",
                connection=cls.connection,
                http_conn_id="http_conn_123",
                endpointurl=cls.endpoint,
                endpoint="/test-endpoint",
                method="POST",
                data={"key": "value"},
                headers={"Content-Type": "application/json"},
                response_check="OK",
                extra_options={"timeout": 10},
                xcom_push=True,
                log_response=False,
                urls=[{"url": "https://example.com"}],
                dag=cls.dag,
            )

    @schema_context(SCHEMA_NAME)
    def test_model_creation(self):
        """Test if SimpleHttpOperatorModel is created correctly."""
        operator = SimpleHttpOperatorModel.objects.get(task_id="test_task")
        self.assertIsNotNone(operator)
        self.assertEqual(operator.endpoint, "/test-endpoint")

    @schema_context(SCHEMA_NAME)
    def test_foreign_key_relationships(self):
        """Ensure foreign keys are correctly assigned."""
        operator = SimpleHttpOperatorModel.objects.get(task_id="test_task")
        self.assertEqual(operator.connection.connection_id, "test_conn_123")
        self.assertEqual(operator.endpointurl.url, "https://api.example.com/test")
        self.assertEqual(operator.dag.dag_id, "test_dag")

    @schema_context(SCHEMA_NAME)
    def test_missing_required_fields(self):
        """Test that creating an object without required fields raises an error."""
        with self.assertRaises(ValidationError):  # Use ValidationError
            obj = SimpleHttpOperatorModel(headers={})  # Required `endpoint`
            obj.full_clean()  # This enforces model field validation


    @schema_context(SCHEMA_NAME)
    def test_str_representation(self):
        """Test that the string representation of the model returns the endpoint value."""
        obj = SimpleHttpOperatorModel.objects.create(
            task_id="task_123",
            connection=self.connection,  
            http_conn_id="http_conn_456",
            endpointurl=self.endpoint,  
            endpoint="test_endpoint",
            method="POST",
            data={"key": "value"},
            headers={"Content-Type": "application/json"},
            response_check="OK",
            extra_options={"timeout": 30},
            xcom_push=True,
            log_response=False,
            dag=self.dag  
        )
        
        self.assertEqual(str(obj), "test_endpoint")  # Expected value


SCHEMA_NAME = os.getenv("SCHEMA_NAME")  

class MediaModelTest(TestCase):

    @classmethod
    @schema_context(SCHEMA_NAME)
    def setUpTestData(cls):
        """Set up test data for the Media model."""
        cls.user = InstagramUser.objects.create(
            username="test_user",
            account_id="123456789",
            source=1,
            scraped=True
        )
        
        cls.media = Media.objects.create(
            media_type="image",
            media_url="https://example.com/media.jpg",
            caption="Test caption",
            user=cls.user,
            timestamp=now(),
            item_id="987654321",
            item_type="photo",
            download_url="https://example.com/download.jpg"
        )

    @schema_context(SCHEMA_NAME)
    def test_media_creation(self):
        """Test that a Media object is created correctly."""
        media = Media.objects.get(id=self.media.id)
        self.assertEqual(media.media_type, "image")
        self.assertEqual(media.media_url, "https://example.com/media.jpg")
        self.assertEqual(media.caption, "Test caption")
        self.assertEqual(media.user, self.user)
        self.assertEqual(media.item_id, "987654321")
        self.assertEqual(media.item_type, "photo")
        self.assertEqual(media.download_url, "https://example.com/download.jpg")

    @schema_context(SCHEMA_NAME)
    def test_str_representation(self):
        """Test the string representation of Media model."""
        self.assertEqual(str(self.media), "https://example.com/media.jpg")

    @schema_context(os.getenv('SCHEMA_NAME'))
    def test_missing_required_fields(self):
        """Test that creating an object without required fields raises a ValidationError."""
        media = Media(media_type="video")  # Missing media_url

        with self.assertRaises(ValidationError):
            media.full_clean()  # Triggers model validation before saving