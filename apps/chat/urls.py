from django.urls import path
from .views import ChatView, ConversationAPIView
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path(
        "app/chat/",
        login_required(ChatView.as_view(template_name="app_chat.html")),
        name="app-chat",
    ),
    path('api/conversations/', ConversationAPIView.as_view(), name='conversations-api'),
]   
