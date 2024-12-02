from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from web_project import TemplateLayout, TemplateHelper

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'ocr/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        return context

class ScanView(LoginRequiredMixin, TemplateView):
    template_name = 'ocr/scan.html'
    
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        return context