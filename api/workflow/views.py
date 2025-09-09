import requests
import json
import os
import uuid
import logging
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.shortcuts import redirect
from django_tenants.utils import schema_context
from django.forms import inlineformset_factory
from django import forms
from django.shortcuts import render
from requests.auth import HTTPBasicAuth
from rest_framework import generics,viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
from django.contrib import messages

from api.workflow.dag_file_handler import push_file,push_file_gcp
from api.workflow.tasks import generate_dag_script

from api.scout.models import Scout
from api.workflow.models import CustomField, CustomFieldValue, Endpoint, HttpOperatorConnectionModel, WorkflowModel, SimpleHttpOperatorModel, DagModel, AirflowCreds
from api.workflow.serializers import (
    CustomFieldSerializer, CustomFieldValueSerializer, EndpointSerializer, 
    HttpOperatorConnectionModelSerializer, WorkflowModelSerializer, SimpleHttpOperatorModelSerializer, DagModelSerializer, AirflowCredsSerializer
)
from api.workflow.forms import (
    CustomFieldForm, CustomFieldValueForm, EndpointForm, HttpOperatorConnectionForm, WorkflowModelForm, SimpleHttpOperatorModelForm, DagModelForm, SimpleHttpOperatorFormSet, DagFormSet, WorkflowRunnerForm
)




# Create your views here.

class PaginationClass(PageNumberPagination):
    page_size = 200  # Set the number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 200




class CustomFieldListCreateView(generics.ListCreateAPIView):
    queryset = CustomField.objects.all()
    serializer_class = CustomFieldSerializer

class CustomFieldRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomField.objects.all()
    serializer_class = CustomFieldSerializer

# Custom Field Value API Views
class CustomFieldValueListCreateView(generics.ListCreateAPIView):
    queryset = CustomFieldValue.objects.all()
    serializer_class = CustomFieldValueSerializer

class CustomFieldValueRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomFieldValue.objects.all()
    serializer_class = CustomFieldValueSerializer

# Endpoint API Views
class EndpointListCreateView(generics.ListCreateAPIView):
    queryset = Endpoint.objects.all()
    serializer_class = EndpointSerializer

class EndpointRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Endpoint.objects.all()
    serializer_class = EndpointSerializer

# Connection API Views
class ConnectionListCreateView(generics.ListCreateAPIView):
    queryset = HttpOperatorConnectionModel.objects.all()
    serializer_class = HttpOperatorConnectionModelSerializer

class ConnectionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = HttpOperatorConnectionModel.objects.all()
    serializer_class = HttpOperatorConnectionModelSerializer

# Workflow API Views
class WorkflowListCreateView(generics.ListCreateAPIView):
    queryset = WorkflowModel.objects.all()
    serializer_class = WorkflowModelSerializer

class WorkflowRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WorkflowModel.objects.all()
    serializer_class = WorkflowModelSerializer

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = WorkflowModel.objects.all()
    serializer_class = WorkflowModelSerializer
    pagination_class = PaginationClass


class CustomFieldCreateView(CreateView):
    model = CustomField
    form_class = CustomFieldForm
    template_name = 'workflows/custom_field_form.html'
    success_url = reverse_lazy('custom_field_list')  # Redirect after creation


class CustomFieldUpdateView(UpdateView):
    model = CustomField
    form_class = CustomFieldForm
    template_name = 'workflows/custom_field_form.html'
    success_url = reverse_lazy('custom_field_list')  # Redirect after creation

class CustomFieldDeleteView(DeleteView):
    model = CustomField
    template_name = 'workflows/custom_field_confirm_delete.html'
    success_url = reverse_lazy('custom_field_list')  # Redirect after deletion

class CustomFieldListView(ListView):
    model = CustomField
    template_name = 'workflows/custom_field_list.html'
    context_object_name = 'custom_fields'

class CustomFieldValueCreateView(CreateView):
    model = CustomFieldValue
    form_class = CustomFieldValueForm
    template_name = 'workflows/custom_field_value_form.html'
    success_url = reverse_lazy('custom_field_list')  # Redirect after creation

    def form_valid(self, form):
        # Associate the custom field value with an endpoint (or other model)
        endpoint_id = self.kwargs['endpoint_id']
        endpoint = Endpoint.objects.get(id=endpoint_id)
        form.instance.content_object = endpoint  # Link to the endpoint
        # Create a JSON-like dictionary for saving
        field_name = form.cleaned_data['field'].name  # Get the name of the selected custom field
        field_value = form.cleaned_data['value']      # Get the input value
        
        # Constructing a dictionary to save as JSON
        json_value = {field_name: field_value}
        
        # Save the constructed JSON object in the value field
        form.instance.value = json_value
        return super().form_valid(form)

class SimpleHttpOperatorViewSet(viewsets.ModelViewSet):
    queryset = SimpleHttpOperatorModel.objects.all()
    serializer_class = SimpleHttpOperatorModelSerializer



class EndpointListView(ListView):
    model = Endpoint
    template_name = 'workflows/endpoint_list.html'  # Template for listing endpoints
    context_object_name = 'endpoints'  # Variable name for the template context

class EndpointCreateView(CreateView):
    model = Endpoint
    form_class = EndpointForm
    template_name = 'workflows/endpoint_form.html'  # Template for creating an endpoint
    success_url = reverse_lazy('endpoint_list')  # Redirect URL after successful creation

class EndpointUpdateView(UpdateView):
    model = Endpoint
    form_class = EndpointForm
    template_name = 'workflows/endpoint_form.html'  # Template for updating an endpoint
    success_url = reverse_lazy('endpoint_list')  # Redirect URL after successful update

class EndpointDeleteView(DeleteView):
    model = Endpoint
    template_name = 'workflows/endpoint_confirm_delete.html'  # Template for confirming deletion
    success_url = reverse_lazy('endpoint_list')  # Redirect URL after successful deletion

class ConnectionListView(ListView):
    model = HttpOperatorConnectionModel
    template_name = 'workflows/connection_list.html'
    context_object_name = 'connections'

class ConnectionCreateView(CreateView):
    model = HttpOperatorConnectionModel
    form_class = HttpOperatorConnectionForm
    template_name = 'workflows/connection_form.html'
    success_url = reverse_lazy('connection_list')
    
    def form_valid(self, form):
        # Save the connection data to the database first
        connection = form.save()

        # Prepare data for Airflow API
        connection_data = {
            "connection_id": connection.connection_id,
            "conn_type": connection.conn_type,
            "host": connection.host,
            "port": connection.port,
            "login": connection.login,
            "password": connection.password,
            # Add other connection details as needed
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Replace with your actual Airflow base URL and credentials
        airflowcred = AirflowCreds.objects.latest('created_at')
        username = airflowcred.username
        password = airflowcred.password

        # Make a POST request to the Airflow API
        response = requests.post(
            f"{airflowcred.airflow_base_url}/api/v1/connections",
            data=json.dumps(connection_data),
            headers=headers,
            auth=HTTPBasicAuth(username, password),
        )

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            messages.success(self.request, "Connection successfully created in both Django and Airflow.")
        else:
            messages.error(self.request, f"Failed to create connection in Airflow: {response.text}")
        return super().form_valid(form)
    
class ConnectionUpdateView(UpdateView):
    model = HttpOperatorConnectionModel
    form_class = HttpOperatorConnectionForm
    template_name = 'workflows/connection_form.html'
    success_url = reverse_lazy('connection_list')

    def form_valid(self, form):
        # Save the connection data to the database first
        connection = form.save()

        # Prepare data for Airflow API
        connection_data = {
            "connection_id": connection.connection_id,
            "conn_type": connection.conn_type,
            "host": connection.host,
            "port": connection.port,
            "login": connection.login,
            "password": connection.password,
            # Add other connection details as needed
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Replace with your actual Airflow base URL and credentials
        airflowcred = AirflowCreds.objects.latest('created_at')
        username = airflowcred.username
        password = airflowcred.password

        # Make a PATCH request to the Airflow API
        response = requests.patch(
            f"{airflowcred.airflow_base_url}/api/v1/connections/{self.object.connection_id}",
            data=json.dumps(connection_data),
            headers=headers,
            auth=HTTPBasicAuth(username, password),
        )

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            messages.success(self.request, "Connection successfully updated in both Django and Airflow.")
        else:
            messages.error(self.request, f"Failed to update connection in Airflow: {response.text}")

        return super().form_valid(form)

class ConnectionDeleteView(DeleteView):
    model = HttpOperatorConnectionModel
    template_name = 'workflows/connection_confirm_delete.html'
    success_url = reverse_lazy('connection_list')

    def form_valid(self, form):
        # Save the connection data to the database first
        
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Replace with your actual Airflow base URL and credentials
        airflowcred = AirflowCreds.objects.latest('created_at')
        username = airflowcred.username
        password = airflowcred.password

        # Make a DELETE request to the Airflow API
        response = requests.delete(
            f"{airflowcred.airflow_base_url}/api/v1/connections/{self.object.connection_id}",
            headers=headers,
            auth=HTTPBasicAuth(username, password),
        )

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            messages.success(self.request, "Connection successfully deleted in both Django and Airflow.")
        else:
            messages.error(self.request, f"Failed to delete connection in Airflow: {response.text}")

        return super().form_valid(form)

class WorkflowInline():
    form_class = WorkflowModelForm
    model = WorkflowModel
    template_name = "workflows/workflow.html"

    # @schema_context("lunyamwi")
    def form_valid(self, form, schema_name=os.getenv('SCHEMA_NAME')):
        with schema_context(schema_name):
            named_formsets = self.get_named_formsets()
            if not all((x.is_valid() for x in named_formsets.values())):
                return self.render_to_response(self.get_context_data(form=form))
            print(self.object,'---object')
            is_update = self.object is not None
            self.object = form.save()
            if is_update:
                dag = self.object.dagmodel_set.latest('created_at')
                try:
                    airflowcreds = AirflowCreds.objects.latest('created_at')
                    headers = {
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    }
                    dag_update_data = {
                        "is_paused": False
                    }

                    try:
                        resp = requests.patch(f"{airflowcreds.airflow_base_url}/api/v1/dags/{dag.dag_id}", 
                                          data=json.dumps(dag_update_data),
                                          auth=HTTPBasicAuth(airflowcreds.username, airflowcreds.password),
                                          headers=headers,timeout=10)
                    except requests.exceptions.Timeout:
                        print("Request timed out")
                    except requests.exceptions.RequestException as e:
                        print(f"An error occurred: {e}")
                    
                    if resp.status_code == 200:
                        messages.success(self.request, f"DAG updated successfully {resp.status_code}")
                    else:
                        messages.error(self.request, f"Failed to update DAG: {resp.status_code}-{resp.text}")
                except Exception as e:
                    messages.error(self.request, f"Failed to update DAG: {str(e)}")
                print("Updating workflow:", self.object)
                logging.warning("updating workflow")
                # Additional logic for updating can go here
            else:
                print("Creating new workflow:", self.object)
                logging.warning("creating new workflow")
                # Additional logic for creation can go here


            # for every formset, attempt to find a specific formset save function
            # otherwise, just save.
            for name, formset in named_formsets.items():
                formset_save_func = getattr(self, 'formset_{0}_valid'.format(name), None)
                if formset_save_func is not None:
                    formset_save_func(formset)
                else:
                    formset.save()
            
            logging.warning(f"Workflow --> {self.object.id}")
            generate_dag_script.delay(self.object.id)
        return redirect('list_workflows')

    def formset_dags_valid(self, formset):
        """
        Hook for custom formset saving.. useful if you have multiple formsets
        """
        dags = formset.save(commit=False)  # self.save_formset(formset, contact)
        # add this, if you have can_delete=True parameter set in inlineformset_factory func
        for obj in formset.deleted_objects:
            obj.delete()
        for dag in dags:
            dag.workflow = self.object
            dag.save()

    def formset_httpoperators_valid(self, formset):
        """
        Hook for custom formset saving.. useful if you have multiple formsets
        """
        httpoperators = formset.save(commit=False)  # self.save_formset(formset, contact)
        # add this, if you have can_delete=True parameter set in inlineformset_factory func
        for obj in formset.deleted_objects:
            obj.delete()
        for operator in httpoperators:
            operator.dag = self.object.dagmodel_set.latest('created_at')
            operator.save()


class WorkflowCreate(WorkflowInline, CreateView):

    def get_context_data(self, **kwargs):
        ctx = super(WorkflowCreate, self).get_context_data(**kwargs)
        ctx['named_formsets'] = self.get_named_formsets()
        return ctx

    def get_named_formsets(self):
        if self.request.method == "GET":
            return {
                'dags': DagFormSet(prefix='dags'),
                'httpoperators': SimpleHttpOperatorFormSet(prefix='httpoperators'),
            }
        else:
            return {
                'dags': DagFormSet(self.request.POST or None, self.request.FILES or None, prefix='dags'),
                'httpoperators': SimpleHttpOperatorFormSet(self.request.POST or None, self.request.FILES or None, prefix='httpoperators'),
            }
        



    
class WorkflowUpdate(WorkflowInline, UpdateView):

    def get_context_data(self, **kwargs):
        ctx = super(WorkflowUpdate, self).get_context_data(**kwargs)
        ctx['named_formsets'] = self.get_named_formsets()
        return ctx

    def get_named_formsets(self):
        return {
            'dags': DagFormSet(self.request.POST or None, self.request.FILES or None, instance=self.object, prefix='dags'),
            'httpoperators': SimpleHttpOperatorFormSet(self.request.POST or None, self.request.FILES or None, instance=self.object.dagmodel_set.latest('created_at'), prefix='httpoperators'),
        }
    



class WorkflowRunner(DetailView):
    model = WorkflowModel
    template_name = "workflows/workflow_runner.html"
    context_object_name = "workflow"
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['workflow'] = self.object
        context['dag'] = self.object.dagmodel_set.latest('created_at')
        # Add the form to the context
        context['form'] = WorkflowRunnerForm()
        return context

    def post(self, request, *args, **kwargs):
        workflow = self.get_object()
        dag_id = workflow.dagmodel_set.latest('created_at').dag_id

        # Create an instance of the form with the POST data
        form = WorkflowRunnerForm(request.POST)
        
        if form.is_valid():
            # Process the form data (e.g., execute the workflow)
            push_to = form.cleaned_data['push_to']
            # You can add logic here based on the value of push_to
            if push_to == 'gcp':
                try:
                    push_file_gcp(filename=dag_id)
                    messages.success(request, "DAG file pushed to GCP successfully.")
                except Exception as e:
                    messages.error(request, f"Failed to push DAG file to GCP: {str(e)}")
            elif push_to == 'ssh':
                try:
                    push_file(filename=dag_id)
                    messages.success(request, "DAG file pushed to SSH successfully.")
                except Exception as e:
                    messages.error(request, f"Failed to push DAG file to SSH: {str(e)}")
            
            # Redirect after processing
            return redirect('workflow_runner', pk=workflow.pk)
        
        # If the form is not valid, re-render the page with the form errors
        return self.render_to_response(self.get_context_data(form=form))
    

class TriggerRun(View):
    
    def get(self, request, *args, **kwargs):
        
        workflow = WorkflowModel.objects.get(id=kwargs['pk'])
        dag_id = workflow.dagmodel_set.latest('created_at').dag_id
        try:
            airflowcreds = AirflowCreds.objects.latest('created_at')
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            dag_update_data = {
                "is_paused": False
            }
            resp = requests.patch(f"{airflowcreds.airflow_base_url}/api/v1/dags/{dag_id}", 
                                    data=json.dumps(dag_update_data),
                                    auth=HTTPBasicAuth(airflowcreds.username, airflowcreds.password),
                                    headers=headers)
            if resp.status_code in [200,201]:
                messages.success(request, "DAG unpaused successfully")
            else:
                messages.error(request, f"Failed to unpause DAG: {resp.text}")
        except Exception as err:
            messages.error(request, f"Failed to unpause DAG: {str(err)}")
        # Trigger the DAG run
        try:
            airflowcreds = AirflowCreds.objects.latest('created_at')
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            dag_run_data = {'conf': {}, 'dag_run_id': f'{dag_id}_{str(uuid.uuid4())}', 'note': None}
            resp = requests.post(
                f"{airflowcreds.airflow_base_url}/api/v1/dags/{dag_id}/dagRuns",
                data=json.dumps(dag_run_data),
                auth=HTTPBasicAuth(airflowcreds.username, airflowcreds.password),
                headers=headers
            )
            if resp.status_code == 200:
                messages.success(request, "DAG run triggered successfully.")
            else:
                messages.error(request, f"Failed to trigger DAG run: {resp.text}")
        except Exception as e:
            messages.error(request, f"Failed to trigger DAG run: {str(e)}")
        
        return redirect('list_workflows')
    

def delete_httpoperator(request, pk):
    try:
        httpOperator = SimpleHttpOperatorModel.objects.get(id=pk)
    except httpOperator.DoesNotExist:
        messages.success(
            request, 'Object Does not exit'
            )
        return redirect('update_workflow', pk=httpOperator.dag.workflow.id)

    httpOperator.delete()
    messages.success(
            request, 'httpOperator deleted successfully'
            )
    return redirect('update_workflow', pk=httpOperator.dag.workflow.id)


def delete_dag(request, pk):
    try:
        dag = DagModel.objects.get(id=pk)
    except dag.DoesNotExist:
        messages.success(
            request, 'Object Does not exit'
            )
        return redirect('update_workflow', pk=dag.workflow.id)

    dag.delete()
    messages.success(
            request, 'dag deleted successfully'
            )
    return redirect('update_workflow', pk=dag.workflow.id)


class WorkflowList(ListView):
    model = WorkflowModel
    template_name = "workflows/workflows.html"
    context_object_name = "workflows"
    
    with schema_context(os.getenv('SCHEMA_NAME')): queryset = WorkflowModel.objects.all()
    

    # @schema_context(os.getenv('SCHEMA_NAME'))
    def get_context_data(self, **kwargs):
        with schema_context(os.getenv('SCHEMA_NAME')):
            print(WorkflowModel.objects.count())
            # context = super().get_context_data(**kwargs)
            context = {}
            context['workflows'] = self.queryset
            print(WorkflowModel.objects.count())
            airflowcreds = AirflowCreds.objects.latest('created_at')
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            context['data'] = []
            try:
                print("Fetching DAGs from Airflow under construction")
                # resp = requests.get(f"{airflowcreds.airflow_base_url}/api/v1/dags", auth=HTTPBasicAuth(airflowcreds.username, airflowcreds.password),headers=headers)   
                # messages.success(self.request, "Fetched DAGs from Airflow successfully.")
                # if resp.status_code == 200:
                #     context['data'] = resp.json()
            except Exception as e:
                messages.error(self.request, f"Failed to fetch DAGs from Airflow: {str(e)}")

            # print(resp.json())
            return context



def display_workflows(request):
    with schema_context(os.getenv('SCHEMA_NAME')):
        workflows = WorkflowModel.objects.all()
        return render(request, 'workflows/workflows.html', {'workflows': workflows})



def generate_workflow(request):
    if request.method == 'POST':
        workflow_form = WorkflowModelForm(request.POST)
        simplehttpoperator_formset = SimpleHttpOperatorFormSet(request.POST)
        dag_formset = DagFormSet(request.POST)
        # import pdb;pdb.set_trace()
        if workflow_form.is_valid() and simplehttpoperator_formset.is_valid() and dag_formset.is_valid():
            workflow = workflow_form.save()
            simplehttpoperators = simplehttpoperator_formset.save()
            dags = dag_formset.save()
            workflow.simplehttpoperators.set(simplehttpoperators)
            for dag in dags:
                workflow.dag = dag  # WorkflowModel.dag is a foreign key
                workflow.save()
            generate_dag_script(workflow)
            return redirect("workflows")  # replace with your actual success page
        
    else:
        workflow_form = WorkflowModelForm()
        simplehttpoperator_formset = SimpleHttpOperatorFormSet(queryset=SimpleHttpOperatorModel.objects.none())
        dag_formset = DagFormSet(queryset=DagModel.objects.none())

    return render(request, 'workflows/workflow.html', {'workflow_form': workflow_form, 'simplehttpoperator_formset': simplehttpoperator_formset, 'dag_formset': dag_formset})
