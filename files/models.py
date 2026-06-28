from django.db import models
from django.conf import settings


class BusinessDocument(models.Model):
    CATEGORY_CHOICES = [
        ('contract', 'Contract'),
        ('invoice', 'Invoice'),
        ('invoice_copy', 'Invoice Copy'),
        ('receipt', 'Receipt'),
        ('permit', 'Permit'),
        ('insurance', 'Insurance Document'),
        ('work_order', 'Work Order'),
        ('estimate', 'Estimate / Quote'),
        ('scan', 'Scanned Document'),
        ('photo', 'Job Photo'),
        ('bank_doc', 'Bank Document'),
        ('tax_doc', 'Tax Document'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    file = models.FileField(upload_to='documents/%Y/%m/', max_length=255)
    description = models.TextField(blank=True, default='')
    customer = models.ForeignKey('core.Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    folder = models.CharField(max_length=200, blank=True, default='')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title
