from django.db import models

class CanvaApp(models.Model):
    name = models.CharField(max_length=255)
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    redirect_uri = models.URLField()
    access_token = models.TextField(blank=True, null=True)
    refresh_token = models.TextField(blank=True, null=True)
    connected = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class CanvaTrigger(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=255)  # design.created, template.opened
    app = models.ForeignKey(CanvaApp, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.app.name} - {self.name}"

class CanvaAction(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    action_type = models.CharField(max_length=255)  # insert_text, apply_brand, export
    app = models.ForeignKey(CanvaApp, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.app.name} - {self.name}"

class CanvaAutomation(models.Model):
    name = models.CharField(max_length=255)
    trigger = models.ForeignKey(CanvaTrigger, on_delete=models.CASCADE)
    action = models.ForeignKey(CanvaAction, on_delete=models.CASCADE)
    conditions = models.JSONField(blank=True, null=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name
