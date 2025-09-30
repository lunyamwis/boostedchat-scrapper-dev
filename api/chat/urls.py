from django.urls import path
from . import views
urlpatterns = [
    path('<str:provider>/', views.chat_interface, name='chat_interface'),
    path('<str:provider>/stop/<str:session_id>/', views.stop_chat_session, name='stop_chat_session'),
    path('<str:provider>/continue/<str:session_id>/', views.continue_chat_session, name='continue_chat_session'),
    path('<str:provider>/add_group/', views.add_group, name='add_group'),  # New URL pattern for adding a group
    path('<str:provider>/groups/', views.chat_groups, name='chat_groups'),
    path('<str:provider>/groups/<int:group_id>/continue/', views.continue_group_listen, name='continue_group_listen'),
    path('<str:provider>/groups/<int:group_id>/stop/', views.stop_group_listen, name='stop_group_listen'),
]