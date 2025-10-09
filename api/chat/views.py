from django.shortcuts import render, redirect
from api.linkedin.models import ChatSession as LinkedInChatSession
from api.whatsapp.models import ChatSession as WhatsAppChatSession, Group as WhatsAppGroup
from api.whatsapp.models import Session as WhatsAppSession

# Create your views here.

def chat_interface(request, provider):
    if provider == 'linkedin':
        chat_sessions = LinkedInChatSession.objects.all()
        return render(request, 'chat/index.html', {'chat_sessions': chat_sessions, 'provider': provider})
    elif provider == 'whatsapp':
        chat_sessions = WhatsAppChatSession.objects.all()
        return render(request, 'chat/index.html', {'chat_sessions': chat_sessions, 'provider': provider})
    else:
        chat_sessions = []
    return render(request, 'chat/index.html', {'chat_sessions': chat_sessions, 'provider': provider})


def stop_chat_session(request, provider, session_id):
    if provider == 'linkedin':
        try:
            chat_session = LinkedInChatSession.objects.get(identifier=session_id)
            chat_session.stop = True
            chat_session.save()
        except LinkedInChatSession.DoesNotExist:
            pass
    elif provider == 'whatsapp':
        try:
            chat_session = WhatsAppChatSession.objects.get(phone=session_id)
            chat_session.stop = True
            chat_session.save()
        except WhatsAppChatSession.DoesNotExist:
            pass
    return redirect('chat_interface', provider=provider)


def continue_chat_session(request, provider, session_id):
    if provider == 'linkedin':
        try:
            chat_session = LinkedInChatSession.objects.get(identifier=session_id)
            chat_session.stop = False
            chat_session.save()
        except LinkedInChatSession.DoesNotExist:
            pass
    elif provider == 'whatsapp':
        try:
            chat_session = WhatsAppChatSession.objects.get(phone=session_id)
            chat_session.stop = False
            chat_session.save()
        except WhatsAppChatSession.DoesNotExist:
            pass
    return redirect('chat_interface', provider=provider)


def add_group(request, provider):
    if request.method == 'POST':
        group_name = request.POST.get('groupName')

        if provider == 'whatsapp':
            print("Creating WhatsApp group with name:", group_name)
            group = WhatsAppGroup.objects.create(name=group_name)

            group.save()
            return redirect('chat_groups', provider=provider)

    return render(request, 'chat/add_group.html', {'provider': provider})


def chat_groups(request, provider):
    if provider == 'whatsapp':
        groups = WhatsAppGroup.objects.all()
        return render(request, 'chat/groups.html', {'groups': groups, 'provider': provider})
    return render(request, 'chat/groups.html', {'groups': [], 'provider': provider})

def continue_group_listen(request, provider, group_id):
    
    if provider == 'whatsapp':
        try:
            group = WhatsAppGroup.objects.get(id=group_id)
            group.listen = True
            group.save()
        except WhatsAppGroup.DoesNotExist:
            pass
    return redirect('chat_groups', provider=provider)

def stop_group_listen(request, provider, group_id):
    if provider == 'whatsapp':
        try:
            group = WhatsAppGroup.objects.get(id=group_id)
            group.listen = False
            group.save()
        except WhatsAppGroup.DoesNotExist:
            pass
    return redirect('chat_groups', provider=provider)


def switch_off_bot(request, provider):
    if provider == 'whatsapp':
        session, created = WhatsAppSession.objects.get_or_create(id=1)
        session.switch_off = True
        session.save()
    return redirect('chat_interface', provider=provider)