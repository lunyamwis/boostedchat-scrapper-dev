import os
import requests

# from setup.token import acquire_token


def detect_intent(project_id, session_id, message, language_code, account_id):
    api_url = (
        f"{os.getenv('DIALOGFLOW_BASE_URL')}agents/{os.getenv('DIALOGFLOW_AGENT_ID')}/sessions/{session_id}:detectIntent"
    )
    # access_token = acquire_token()  # Replace with your actual access token
    access_token = "your_access_token_here"  # Replace with your actual access token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "queryInput": {
            "languageCode": language_code,
            "text": {
                "text": message
            },
        },
        "queryParams": {
            "payload": {
                "account_id": account_id,
            }
        }
        }
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception if response status is not 2xx
        response_data = response.json()
        print("<<<<Response>>>>", flush=True)
        print(response_data, flush=True)
        print("<<<<Response>>>>", flush=True)
        fulfillment_text = response_data["queryResult"]["responseMessages"][0].get("text").get("text")
        print("<<<<Fulfill>>>>", flush=True)
        print(fulfillment_text, flush=True)
        print("<<<<fulfil>>>>", flush=True)
        return fulfillment_text
    except requests.exceptions.RequestException as error:
        error_message = str(error)
        return {"error": error_message}
