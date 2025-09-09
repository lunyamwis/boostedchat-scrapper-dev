from django.db import models
from api.helpers.models import BaseModel
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField


# Create your models here.
class AirflowCreds(BaseModel):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    schema_name = models.CharField(max_length=255)
    airflow_base_url = models.URLField()

    def __str__(self) -> str:
        return self.schema_name

class WorkflowModel(BaseModel):
    WORKFLOW_CHOICES = (
        ("simple_httpoperators_sequential_with_condition","chain the endpoints but initialize with a condition to be checked in order for it to begin running"),
        ("simple_httpoperators_sequential_run","chain the endpoints and run them sequentially in a linear fashion"),
        ("simple_httpoperators_parallel_run","chain the endpoints and run them in a parallel manner")
    )
    name = models.CharField(max_length=255,null=True, blank=True)
    delay_durations = models.JSONField(null=True,blank=True)
    airflow_creds = models.ForeignKey(AirflowCreds,on_delete=models.CASCADE,null=True, blank=True)
    workflow_type = models.CharField(max_length=255, choices=WORKFLOW_CHOICES, default="simple_httpoperators_sequential_run")

class HttpOperatorConnectionModel(BaseModel):
    connection_id = models.CharField(max_length=255)
    conn_type = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.IntegerField(null=True,blank=True)
    login = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.connection_id

class DagModel(BaseModel):
    dag_id = models.CharField(max_length=255)
    description = models.TextField()
    schedule = models.CharField()
    schedule_interval = models.CharField(max_length=255)
    timetable = models.CharField(max_length=255,null=True,blank=True)
    start_date = models.DateTimeField(null=True,blank=True)
    end_date = models.DateTimeField(null=True,blank=True)
    full_filepath = models.CharField(max_length=255,null=True,blank=True)
    template_searchpath = models.CharField(null=True,blank=True)
    template_undefined = models.TextField(null=True,blank=True)
    user_defined_macros  = models.JSONField(null=True,blank=True)
    user_defined_filters = models.JSONField(null=True,blank=True)
    default_args = models.JSONField(null=True,blank=True)
    concurrency = models.IntegerField(null=True,blank=True)
    max_active_tasks = models.IntegerField(null=True,blank=True)
    max_active_runs = models.IntegerField(null=True,blank=True)
    dagrun_timeout = models.DateTimeField(null=True,blank=True)
    sla_miss_callback = models.TextField(null=True,blank=True)
    default_view = models.CharField(max_length=255,null=True,blank=True)
    orientation = models.CharField(max_length=255,null=True,blank=True)
    catchup = models.BooleanField(default=False)
    on_success_callback = models.TextField(null=True,blank=True)
    on_failure_callback = models.TextField(null=True,blank=True)
    doc_md = models.CharField(max_length=255,null=True,blank=True)
    params = models.JSONField(null=True,blank=True)
    access_control = models.JSONField(null=True,blank=True)
    is_paused_upon_creation = models.BooleanField(default=False)
    jinja_environment_kwargs = models.JSONField(null=True,blank=True)
    render_template_as_native_obj = models.BooleanField(default=False)
    tags = ArrayField(models.CharField(max_length=50), blank=True, null=True)
    owner_links = models.JSONField(null=True,blank=True)
    auto_register = models.BooleanField(default=False)
    fail_stop = models.BooleanField(default=False)
    trigger_url = models.CharField(null=True,blank=True,max_length=255)
    connection = models.ForeignKey(HttpOperatorConnectionModel,on_delete=models.CASCADE,null=True, blank=True)
    trigger_url_expected_key = models.CharField(null=True,blank=True,max_length=255)
    trigger_url_expected_value = models.CharField(null=True,blank=True,max_length=255)
    workflow = models.ForeignKey(WorkflowModel,on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self) -> str:
        return self.dag_id


class CustomField(BaseModel):
    name = models.CharField(max_length=255)
    data_type = models.CharField(max_length=50, choices=[
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Boolean'),
        ('json', 'JSON')
    ])

    def __str__(self):
        return self.name

class CustomFieldValue(BaseModel):
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(null=True, blank=True, max_length=255)
    content_object = GenericForeignKey('content_type', 'object_id')
    value = models.JSONField()

    def __str__(self):
        return f"{self.field.name}: {self.value}"

    
class Endpoint(BaseModel):
    base_url = models.URLField(null=True,blank=True)
    url = models.CharField(null=True,blank=True)
    method = models.CharField(max_length=10, choices=(('GET','GET'), ('POST','POST')),default='GET')
    
    def __str__(self):
        return self.url

    @property
    def custom_fields(self):
        return CustomFieldValue.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id)

class PostgresOperatorModel(BaseModel):
    task_id = models.CharField(max_length=255,null=True, blank=True)
    connection = models.ForeignKey(HttpOperatorConnectionModel,on_delete=models.CASCADE,null=True, blank=True)
    sql = models.TextField()
    autocommit = models.BooleanField(default=False)
    parameters = models.JSONField(null=True,blank=True)
    dag = models.ForeignKey(DagModel,on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self) -> str:
        return self.task_id

class SimpleHttpOperatorModel(BaseModel):
    METHODS = (
        ("GET","GET"),
        ("POST","POST")
    )
    task_id = models.CharField(max_length=255,null=True, blank=True)
    connection = models.ForeignKey(HttpOperatorConnectionModel,on_delete=models.CASCADE,null=True, blank=True)
    http_conn_id=models.CharField(max_length=144,default="your_http_connection")
    endpointurl = models.ForeignKey(Endpoint,on_delete=models.CASCADE,null=True, blank=True)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=20, choices=METHODS, default="POST")
    data = models.JSONField(null=True,blank=True)
    headers = models.JSONField()
    response_check = models.CharField(max_length=1024,null=True,blank=True)
    extra_options = models.JSONField(null=True,blank=True)
    xcom_push = models.BooleanField(default=True)
    log_response = models.BooleanField(default=False)
    urls = ArrayField(models.JSONField(null=True, blank=True), blank=True, null=True)
    dag = models.ForeignKey(DagModel,on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self) -> str:
        return self.endpoint
