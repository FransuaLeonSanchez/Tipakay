# TechPro Store WhatsApp Bot

Bot de WhatsApp integrado con OpenAI y Twilio diseñado para TechPro Store. Gestiona automáticamente las consultas de productos, pedidos y atención al cliente. El bot maneja el catálogo de productos, sistema de envíos basado en ubicación, procesos de pago y almacena el historial de conversaciones en PostgreSQL para una experiencia personalizada.

## Estructura del Proyecto

- main.py: Servidor FastAPI y punto de entrada
- llm.py: Integración con OpenAI
- twilio_chat.py: Manejo de mensajes de WhatsApp
- database.py: Operaciones con la base de datos
- config.py: Configuración del sistema y prompt del bot
- Dockerfile: Configuración para Docker
- .env.example: Ejemplo de variables de entorno necesarias

## Ejecución Local

1. Instalar dependencias:
pip install -r requirements.txt

2. Copiar .env.example a .env y configurar las variables

3. Ejecutar el servidor:
python main.py

## Ejecución con Docker

1. Construir la imagen de Docker:
```bash
docker build -t tipakay .
```

2. Ejecutar el contenedor en segundo plano:
```bash
docker run -d --name docker_tipakay -p 5000:5000 tipakay
```

Comandos útiles de Docker:
```bash
# Ver logs del contenedor
docker logs docker_tipakay

# Detener el contenedor
docker stop docker_tipakay

# Reiniciar el contenedor
docker restart docker_tipakay

# Eliminar el contenedor
docker rm docker_tipakay
```

## Funcionalidades del Bot

- Saludo inicial automático
- Catálogo de productos con precios
- Gestión de pedidos
- Sistema de envíos para diferentes ciudades
- Manejo de pagos (contra entrega o adelanto según ubicación)
- Respuestas a preguntas frecuentes
- Historial de conversaciones