# dockerapp/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RestartContainerSerializer
import docker


class ForceRecreateApi(APIView):
    def post(self, request):
        container_id = 'boostedchat-site-api-1'  # Assuming this is a fixed container name

        try:
            # Create a Docker client
            client = docker.from_env()

            # Get the specified container
            container = client.containers.get(request.data.get('container_id'))

            # Stop the container
            container.stop()

            # Remove the container
            container.remove()

            # Pull the latest image
            container_image = request.data.get('container_image')
            client.images.pull(container_image)

            # Create a new container
            container = client.containers.run(
                container_image,
                detach=True,
                name=container_id,
                ports={'8000/tcp': 8000},
                volumes={'/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'}}
            )

            return Response({"message": f"Container '{container_id}' recreated successfully."}, status=status.HTTP_200_OK)
        except docker.errors.NotFound:
            return Response({"error": "Container not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class RestartContainerView(APIView):
    def post(self, request):
        serializer = RestartContainerSerializer(data=request.data)
        
        if serializer.is_valid():
            container_id = serializer.validated_data['container_id']
            try:
                # Create a Docker client
                client = docker.from_env()

                # Get the specified container
                container = client.containers.get(container_id)

                # Restart the container
                container.restart()
                

                return Response({"message": f"Container '{container_id}' restarted successfully."}, status=status.HTTP_200_OK)
            except docker.errors.NotFound:
                return Response({"error": "Container not found."}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetConversationsView(APIView):
    def post(self, request):
        container_id = 'boostedchat-site-api-1'  # Assuming this is a fixed container name

        try:
            # Create a Docker client
            client = docker.from_env()

            # Get the specified container
            container = client.containers.get(container_id)

            # Command to execute inside the container
            command = (
                "python manage.py shell -c "
                "'from api.instagram.models import Account; "
                "account = Account.objects.get(igname=\"psychologistswithoutborders\"); "
                "thread = account.thread_set.latest(\"created_at\"); "
                "thread.message_set.clear()'"
            )
            
#             python manage.py shell -c 'from api.instagram.models import Account; 
# account = Account.objects.get(igname="psychologistswithoutborders"); 
# thread = account.thread_set.latest("created_at");
# thread.message_set.count()'

            # Execute the command in the container
            exec_log = container.exec_run(command, stderr=True, stdout=True)

            if exec_log.exit_code == 0:
                return Response({"message": f"Conversations reset successfully. {exec_log.output.decode('utf-8')}"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": exec_log.output.decode('utf-8')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except docker.errors.NotFound:
            return Response({"error": "Container not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)