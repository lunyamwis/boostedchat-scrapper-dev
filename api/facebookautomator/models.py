from django.db import models


# Create your models here.
class ChatSession(models.Model):
    recipient_id = models.CharField(max_length=255, unique=True)
    conversation_history = models.JSONField(default=list)

    def __str__(self):
        return self.id
    
      
    def add_message(self, role, content):
        self.conversation_history.append({"role": role, "content": content})
        self.save()