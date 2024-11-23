from django.db import models


class LLMRole(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    prompt_template = models.TextField()
    model_name = models.CharField(max_length=100, default="gpt-3.5-turbo")
    max_tokens = models.IntegerField(default=150)
    temperature = models.FloatField(default=0.7)
    collaborators = models.ManyToManyField(
        "self",
        symmetrical=False,  # A->B doesn't mean B->A
        blank=True,
        related_name="can_collaborate_with",
    )
    # Optional: Add collaboration triggers/rules
    collaboration_triggers = models.TextField(
        blank=True,
        help_text="Keywords or patterns that suggest collaboration with this role",
    )

    def __str__(self):
        return self.name
