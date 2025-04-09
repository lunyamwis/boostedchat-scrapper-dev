from django.db import models

# Create your models here.
class ChatSession(models.Model):
    phone = models.CharField(max_length=20, unique=True)
    conversation_history = models.JSONField(default=list)

    def __str__(self):
        return self.phone
      
    def add_message(self, role, content):
        self.conversation_history.append({"role": role, "content": content})
        self.save()