from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from web_project import TemplateLayout
from django.http import JsonResponse
from openai import OpenAI
from django.conf import settings
import base64
import json
import logging
from datetime import datetime
import re
import tempfile
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from .huawei_obs import HuaweiOBSUploader
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

def standardize_date(date_str):
    """
    Convierte diferentes formatos de fecha a YYYY-MM-DD
    """
    try:
        formats = [
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%Y %b %d',
            '%d.%m.%Y'
        ]
        
        if re.match(r'^\d{4}\s+[A-Za-z]+\s+\d{1,2}$', date_str):
            parts = date_str.split()
            month_map = {
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
            }
            month = month_map.get(parts[1][:3].capitalize(), '01')
            return f"{parts[0]}-{month}-{int(parts[2]):02d}"
        
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
            
        if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
            day, month, year = date_str.split('/')
            return f"{year}-{month}-{day}"
            
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        raise ValueError(f"No se pudo convertir la fecha: {date_str}")
    except Exception as e:
        logger.error(f"Error al estandarizar fecha {date_str}: {str(e)}")
        return date_str

def process_image_with_openai(image_file):
    """
    Procesa una imagen usando OpenAI Vision
    """
    try:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key no configurada")
        
        if image_file.size > 20 * 1024 * 1024:
            raise ValueError("La imagen es demasiado grande. Máximo 20MB permitido.")
            
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if image_file.content_type not in allowed_types:
            raise ValueError(f"Tipo de archivo no permitido. Use: {', '.join(allowed_types)}")
            
        image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        logger.info("Enviando imagen a OpenAI...")
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Extract the following information from the table in the image:
                    - numero (N° column)
                    - name (Name/Nombre column)
                    - category (Category/Categoría column)
                    - insertion_date (Date/Fecha column as shown)
                    - address (Address/Dirección column, if present)
                    
                    Format the output as a JSON with a 'records' array."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract the information from this table as JSON."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            response_format={ "type": "json_object" },
            max_tokens=1000,
        )
        
        result = completion.choices[0].message.content
        logger.info(f"Respuesta de OpenAI recibida: {result}")
        
        parsed_result = json.loads(result)
        
        for record in parsed_result.get('records', []):
            if 'insertion_date' in record:
                record['insertion_date'] = standardize_date(record['insertion_date'])
        
        return parsed_result
        
    except Exception as e:
        logger.error(f"Error en process_image_with_openai: {str(e)}")
        raise

def process_and_save_records(result):
    """
    Procesa y guarda los registros OCR en la base de datos PostgreSQL
    """
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()

        saved_records = []
        for record in result.get('records', []):
            query = """
            INSERT INTO ocr_records (numero, name, category, insertion_date, address)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, numero, name, category, insertion_date, address;
            """
            
            cursor.execute(query, (
                record['numero'],
                record['name'],
                record['category'],
                record['insertion_date'],
                record.get('address', '')
            ))
            
            saved_record = cursor.fetchone()
            saved_records.append(dict(saved_record))

        conn.commit()
        return saved_records

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error guardando registros OCR: {str(e)}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def list_bucket_images(request):
    """
    Lista todas las imágenes del bucket Huawei OBS
    """
    try:
        uploader = HuaweiOBSUploader()
        images = uploader.list_images()
        return JsonResponse({
            "images": [{
                'url': img['url'],
                'name': img['name'],
                'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            } for img in images]
        })
    except Exception as e:
        logger.error(f"Error listing bucket images: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

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
    
    def post(self, request, *args, **kwargs):
        try:
            if not request.FILES.get('document'):
                return JsonResponse({'error': 'No se ha proporcionado ninguna imagen'}, status=400)
            
            image_file = request.FILES['document']
            
            # Procesar con OpenAI
            result = process_image_with_openai(image_file)
            
            # Subir imagen a Huawei OBS
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in image_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                uploader = HuaweiOBSUploader()
                public_url = uploader.upload_image(
                    temp_file_path,
                    original_filename=image_file.name
                )
                
                if not public_url:
                    raise ValueError("Error al subir archivo a Huawei OBS")

                # Añadir la URL del documento al resultado
                result['document_url'] = public_url
                
                # Guardar registros en la base de datos
                saved_records = process_and_save_records(result)
                result['records'] = saved_records
                    
            finally:
                os.unlink(temp_file_path)
            
            return JsonResponse(result)
                
        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)