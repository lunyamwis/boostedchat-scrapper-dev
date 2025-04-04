import logging
import os
import re
import json

import requests
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.dialogflow.helpers.get_prompt_responses import get_gpt_response
from api.instagram.models import Account, Message, Thread


class FallbackWebhook(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def post(self, request, format=None):

        thread = Thread()

        try:
            req = request.data
            query_result = req.get("fulfillmentInfo")

            query = req.get("text")

            account_id = req.get("payload").get("account_id")

            if query_result.get("tag") == "fallback":
                account = Account.objects.get(id=account_id)
                thread = Thread.objects.filter(account=account).last()
                
                client_messages = query.split("#*eb4*#")
                for client_message in client_messages:
                    Message.objects.create(
                        content = client_message,
                        sent_by = "Client",
                        sent_on = timezone.now(),
                        thread = thread
                    )
                thread.last_message_content = client_messages[len(client_messages)-1]
                thread.unread_message_count = len(client_messages)
                thread.last_message_at = timezone.now()
                thread.save()
                
                gpt_resp = get_gpt_response(account, thread.thread_id)

                thread.last_message_content = gpt_resp.get('text')
                thread.last_message_at = timezone.now()
                thread.save()

                result = gpt_resp.get('text')
                Message.objects.create(
                    content = result,
                    sent_by = "Robot",
                    sent_on = timezone.now(),
                    thread = thread
                )
                
                return Response(
                    {
                        "fulfillment_response": {
                            "messages": [
                                {
                                    "text": {
                                        "text": [result],
                                    },
                                },
                            ]
                        }
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as error:
            print(error)
            return Response(
                {
                    "fulfillment_response": {
                        "messages": [
                            {
                                "text": {
                                    "text": ["Come again"],
                                },
                            },
                        ]
                    }
                },
                status=status.HTTP_200_OK,
            )
