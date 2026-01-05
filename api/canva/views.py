import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CanvaAutomation
from .tasks import execute_canva_automation

def plugin_sidebar(request):
    """Render the Canva plugin sidebar"""
    automations = CanvaAutomation.objects.filter(enabled=True)
    return render(request, "canva/plugin_sidebar.html", {"automations": automations})

@csrf_exempt
def execute_automation(request):
    """Receive AJAX requests from sidebar buttons"""
    try:
        data = json.loads(request.body)
        automation_id = data.get("automation_id")
        design_id = data.get("design_id")
        user_inputs = data.get("user_inputs", {})

        execute_canva_automation.delay(automation_id, design_id, user_inputs)
        return JsonResponse({"status": "Automation queued!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@csrf_exempt
def canva_webhook(request):
    """Webhook for Canva events"""
    try:
        payload = json.loads(request.body)
        event_type = payload.get("event_type")
        design_id = payload.get("design_id")

        automations = CanvaAutomation.objects.filter(trigger__event_type=event_type, enabled=True)
        for auto in automations:
            execute_canva_automation.delay(auto.id, design_id, payload)
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
