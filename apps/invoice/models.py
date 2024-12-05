from django.db import models

class OCRRecord(models.Model):
    numero = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    insertion_date = models.DateField()
    address = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'ocr_records'  # Especificamos el nombre exacto de la tabla
        
    def __str__(self):
        return f"{self.name} - {self.numero}"