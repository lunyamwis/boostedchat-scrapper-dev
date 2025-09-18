from django_tenants.utils import schema_context
import os
import requests
import logging
from api.whatsapp.models import ChatSession
from api.prompt.models import Prompt


@schema_context(os.getenv('SCHEMA_NAME'))
def query_gpt(user_input,phone_number=None):
    # declare chat_session variable
    system_prompt = Prompt.objects.filter(channel='whatsapp').latest('created_at').text_data
    chat_session= None
    if phone_number is not None:
        try:
            # Check if session exists
            conversation_history=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ]
            chat_session = ChatSession.objects.get(phone=phone_number)
            chat_session.conversation_history = conversation_history
            chat_session.save()
            chat_session.add_message("user", user_input)
        except ChatSession.DoesNotExist:
            conversation_history=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ]
            chat_session = ChatSession.objects.create(
                phone=phone_number,
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

    return res.json()
