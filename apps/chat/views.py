from django.views.generic import TemplateView
from django.views import View
from django.http import JsonResponse
from .models import Conversation
from web_project import TemplateLayout

class ChatView(TemplateView):
    template_name = "app_chat.html"
    
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        return context

class ConversationAPIView(View):
    def get(self, request):
        try:
            conversations = Conversation.objects.using('huawei_db').all().values(
                'id_chat', 
                'phone_number', 
                'chat_history'
            )
            print("Conversaciones encontradas:", conversations)  # Debug
            return JsonResponse({"conversations": list(conversations)})
        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({"error": str(e)}, status=500)