from django.views.generic import TemplateView
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper
from django.http import JsonResponse
from django.views import View
from .models import OCRRecord
from django.core.serializers import serialize
import json

from django.http import JsonResponse
from django.views import View
from django.db import connection, connections  # Agregamos el import correcto
from django.forms.models import model_to_dict

"""
This file is a view controller for multiple pages as a module.
Here you can override the page view layout.
Refer to invoice/urls.py file for more pages.
"""


class InvoiceView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        return context


class InvoicePrintView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        # Update the context
        context.update(
            {
                "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
            }
        )

        return context


class OCRRecordListView(View):
    def get(self, request):
        try:
            with connections['huawei_db'].cursor() as cursor:
                cursor.execute("""
                    SELECT id, numero, name, category, insertion_date, address 
                    FROM ocr_records 
                    ORDER BY insertion_date DESC
                """)
                rows = cursor.fetchall()
                
                # Get column names from cursor.description
                columns = [col[0] for col in cursor.description]
                
                # Format the data as a list of dictionaries
                data = []
                for row in rows:
                    # Convertir la fecha a string si es necesario
                    row_data = list(row)
                    if row_data[4]:  # índice de insertion_date
                        row_data[4] = row_data[4].strftime('%Y-%m-%d')
                    data.append(dict(zip(columns, row_data)))
                
                return JsonResponse({'data': data})
                
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'status': 'error',
                'type': str(type(e))  # Esto nos ayudará a identificar el tipo exacto de error
            }, status=500)
