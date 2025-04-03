from django.db.models import Q

from api.instagram.models import Message


def get_conversation_so_far(thread_id):
    messages = Message.objects.filter(thread__thread_id=thread_id)
    print("conversation so far")
    print(thread_id)
    print(messages)
    print("conversation so far")
    formatted_messages = []
    for message in messages:
        formatted_message = ""
        if message.sent_by == "Client":
            formatted_message = f"Respondent: {message.content}"
        else:
            formatted_message = f"You: {message.content}"
        formatted_messages.append(formatted_message)
    return "\n".join(formatted_messages)


def get_client_conversation_so_far(thread_id):
    client_messages = Message.objects.filter(Q(thread__thread_id=thread_id) & Q(sent_by="Client")).order_by("-sent_on")
    print("client messages so far")
    print(thread_id)
    print(client_messages)
    print("client messages so far")
    formatted_messages = []
    if client_messages.exists():
        messages = Message.objects.all()
        for message in messages:
            formatted_message = ""
            if message.sent_by == "Client":
                formatted_message = f"Respondent: {message.content}"
            else:
                formatted_message = f"You: {message.content}"
            formatted_messages.append(formatted_message)
        return "\n".join(formatted_messages)
