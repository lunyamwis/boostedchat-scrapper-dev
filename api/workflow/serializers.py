import json
import os
import yaml
from rest_framework import serializers
from django.conf import settings
from .models import (
    CustomField,
    CustomFieldValue,
    Endpoint,
    HttpOperatorConnectionModel,
    WorkflowModel,  
    DagModel,
    SimpleHttpOperatorModel,
    AirflowCreds
)
from api.workflow.dag_generator import generate_dag  

class AirflowCredsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirflowCreds
        fields = '__all__'


class CustomFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomField
        fields = '__all__'

class CustomFieldValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFieldValue
        fields = '__all__'

class EndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Endpoint
        fields = '__all__'

class HttpOperatorConnectionModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = HttpOperatorConnectionModel
        fields = '__all__'

class WorkflowModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowModel
        fields = '__all__'

class DagModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DagModel
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }

class SimpleHttpOperatorModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimpleHttpOperatorModel
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
            "data": {"required": False, "allow_null": True},
        }

class WorkflowModelSerializer(serializers.ModelSerializer):
    simplehttpoperators = SimpleHttpOperatorModelSerializer(many=True, required=False)
    dag = DagModelSerializer(required=False)

    class Meta:
        model = WorkflowModel
        fields = ['id', 'name', 'simplehttpoperators','dag','delay_durations']
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }
    
    def create(self, validated_data):
        simplehttpoperators_data = validated_data.pop('simplehttpoperators', [])
        dag_data = validated_data.pop('dag', None)
        data = None

        workflow = super().create(validated_data)

        for simplehttpoperator_data in simplehttpoperators_data:
            if "urls" in simplehttpoperator_data:
                simplehttpoperator_data['urls'] = [json.dumps(urls_data) for urls_data in simplehttpoperator_data['urls']] 
            simplehttpoperator, _ = SimpleHttpOperatorModel.objects.get_or_create(**simplehttpoperator_data)
            workflow.simplehttpoperators.add(simplehttpoperator)

        if dag_data:
            dag, _ = DagModel.objects.get_or_create(**dag_data)
            workflow.dag = dag
            workflow.save()

        if "trigger_url" in dag_data:
        
            data = {
                "dag":[entry for entry in DagModel.objects.filter(id = workflow.dag.id).values()],
                "operators":[entry for entry in workflow.simplehttpoperators.values()],
                "data_seconds":workflow.delay_durations,
                "trigger_url":dag_data.get("trigger_url"),
                "trigger_url_expected_response":dag_data.get("trigger_url_expected_response")
            }
        else:
            data = {
                "dag":[entry for entry in DagModel.objects.filter(id = workflow.dag.id).values()],
                "operators":[entry for entry in workflow.simplehttpoperators.values()],
                "data_seconds":workflow.delay_durations
            }

        
        # Write the dictionary to a YAML file
        yaml_file_path = os.path.join(settings.BASE_DIR, 'api', 'helpers', 'include', 'dag_configs', f"{workflow.dag.dag_id}_config.yaml")
        with open(yaml_file_path, 'w') as yaml_file:
            try:
                yaml.dump(data, yaml_file, default_flow_style=False)
            except Exception as error:
                raise serializers.ValidationError(str(error))

        try:
            generate_dag()
        except Exception as error:
            raise serializers.ValidationError(str(error))

        return workflow
