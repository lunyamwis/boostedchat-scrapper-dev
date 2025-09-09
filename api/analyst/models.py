from django.db import models

from django.contrib.contenttypes.models import ContentType

# Create your models here.
class DatabaseCred(models.Model):
    name = models.CharField(max_length=200)
    value = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    


class DataEntry(models.Model):
    CHARTTYPES = (
        ('line','Line'),
        ('bar','Bar'),
        ('pie','Pie'),
    )
    name = models.CharField(max_length=200)
    chart_type = models.CharField(max_length=200,choices=CHARTTYPES,default='line')
    query = models.TextField()

    
    def __str__(self) -> str:
        return self.name if self.name else self.id