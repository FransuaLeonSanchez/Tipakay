# models.py
from django.db import models

class Conversation(models.Model):
    id_chat = models.AutoField(primary_key=True)
    phone_number = models.BigIntegerField()  # Cambiado a BigIntegerField para números grandes
    chat_history = models.TextField()

    class Meta:
        db_table = 'conversations'
        ordering = ['-id_chat']  # Ordenar por id en lugar de created_at
        managed = False  # Importante: indica que Django no maneje esta tabla

    def __str__(self):
        return f"Chat {self.id_chat} - {self.phone_number}"