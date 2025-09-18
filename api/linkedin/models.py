from django.db import models

# Create your models here.
class ChatSession(models.Model):
    identifier = models.CharField(max_length=255, null=True, blank=True)
    conversation_history = models.JSONField(default=list)
    stop = models.BooleanField(default=False)

    def __str__(self):
        return str(self.identifier)

    def add_message(self, role, content):
        self.conversation_history.append({"role": role, "content": content})
        self.save()