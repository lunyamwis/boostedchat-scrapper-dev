from django_tenants.utils import schema_context
import os
import requests
import logging
from api.facebookautomator.models import ChatSession
from api.prompt.models import Prompt

def query_gpt(prompt,recipient_id=None, schema_name=None):
    # declare chat_session variable
    with schema_context(schema_name):
        system_prompt = Prompt.objects.filter(channel='facebook').latest('created_at').text_data
        chat_session= None
        if recipient_id is not None:
            try:
                # Check if session exists
                chat_session = ChatSession.objects.get(recipient_id=recipient_id)
                chat_session.add_message("user", prompt)
            except ChatSession.DoesNotExist:
                conversation_history=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ]
                chat_session = ChatSession.objects.create(
                    recipient_id=recipient_id,
                    conversation_history=conversation_history
                )
        body = {
            "model": "gpt-4-1106-preview",
            "messages": chat_session.conversation_history,
        }
        header = {"Authorization": "Bearer " + os.getenv("OPENAI_API_KEY").strip()}

        res = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=header)
        # save the response to the database
        gpt_response = res.json()["choices"][0]["message"]["content"]
        chat_session.add_message("system", gpt_response)
        logging.warn(str(["time elapsed", res.elapsed.total_seconds()]))

        return gpt_response

