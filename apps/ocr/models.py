from django.db import models

class OCRRecord(models.Model):
    numero = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    insertion_date = models.DateField()
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    document_url = models.URLField(max_length=500, blank=True, null=True)  # Added for Huawei OBS URL

    class Meta:
        managed = False
        db_table = 'ocr_records'
        ordering = ['numero']

    def __str__(self):
        return f"{self.numero} - {self.name}"