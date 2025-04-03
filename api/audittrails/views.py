import json
from rest_framework.decorators import api_view
from auditlog.models import LogEntry
from rest_framework import status, viewsets
from rest_framework.response import Response

from .serializers import LogEntrySerializer

# Create your views here.


class LogEntryViewset(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer

    def list(self, request, *args, **kwargs):
        entries = []

        print(len(self.queryset))
        for entry in self.queryset:

            if entry:
                if entry.actor:
                    entry_dict = {
                        "object_pk": entry.object_pk,
                        "timestamp": entry.timestamp,
                        "actor": f"{entry.actor.first_name} {entry.actor.last_name}",
                        "actor_email": entry.actor.email,
                        "action": entry.action,
                        "changes": entry.changes,
                    }
                else:
                    entry_dict = {
                        "object_pk": entry.object_pk,
                        "timestamp": entry.timestamp,
                        "action": entry.action,
                        "changes": entry.changes,
                    }
            else:
                return Response(self.queryset.values)
            entries.append(entry_dict)

        return Response(entries, status=status.HTTP_200_OK)


@api_view(['GET'])
def status_log_entries_by_account(request, account_id):
    entries = []
    log_entries = LogEntry.objects.filter(object_pk=account_id).order_by("timestamp")

    print(len(log_entries))
    for entry in log_entries:

        if entry:
            changes_object = json.loads(entry.changes)
            if changes_object.get("status"):
                entry_dict = {
                    "object_pk": entry.object_pk,
                    "timestamp": entry.timestamp,
                    "action": entry.action,
                    "changes": entry.changes,
                }
                entries.append(entry_dict)
        else:
            return Response([], status=status.HTTP_200_OK)

    return Response(entries, status=status.HTTP_200_OK)
