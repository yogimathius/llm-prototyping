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


class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(LLMRole, on_delete=models.CASCADE)
    prompt = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
