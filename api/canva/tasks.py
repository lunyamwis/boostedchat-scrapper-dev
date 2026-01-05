from celery import shared_task
from .models import CanvaAutomation
from api.canva.services.canva_api import CanvaAPI

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60)
def execute_canva_automation(self, automation_id, design_id, user_inputs):
    automation = CanvaAutomation.objects.get(id=automation_id)
    action = automation.action
    api = CanvaAPI(automation.trigger.app)

    # Example actions
    if action.action_type == "insert_text":
        text = user_inputs.get("text", "Hello from plugin!")
        api.insert_text_element(design_id, text)

    elif action.action_type == "update_text":
        text = user_inputs.get("text", "Updated text")
        api.update_text(design_id, text)

    elif action.action_type == "export_design":
        file_url = api.export_design(design_id)
        # You can store file_url or send via email

    elif action.action_type == "apply_brand":
        brand_kit_id = user_inputs.get("brand_kit_id")
        api.apply_brand(design_id, brand_kit_id)

    else:
        raise ValueError(f"Unknown action type: {action.action_type}")
