from django.db import models
from api.instagram.models import Account
from api.sales_rep.models import SalesRep

class OutreachErrorLog(models.Model):
    LOG_LEVEL_CHOICES = (
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
    )

    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    sales_rep = models.ForeignKey(SalesRep, on_delete=models.SET_NULL, null=True, blank=True)
    code = models.IntegerField()
    error_message = models.TextField()
    error_type = models.TextField()
    log_level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES, default='ERROR')
    created_at = models.DateTimeField(auto_now_add=True)

    def save_log(self, code, error_message, error_type, log_level, account=None, sales_rep=None):
        self.code = code
        self.error_message = error_message
        self.log_level = log_level
        self.error_type = error_type
        if account:
            self.account = account
        if sales_rep:
            self.sales_rep = sales_rep
        self.save()

    @classmethod
    def get_logs(cls):
        return cls.objects.all()
        
