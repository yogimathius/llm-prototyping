from django.db import models

class LLMRole(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    prompt_template = models.TextField()
    model_name = models.CharField(max_length=100, default="gpt-3.5-turbo")
    max_tokens = models.IntegerField(default=150)
    temperature = models.FloatField(default=0.7)

    def __str__(self):
        return self.name
