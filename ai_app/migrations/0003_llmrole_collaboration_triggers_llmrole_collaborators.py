# Generated by Django 5.1.2 on 2024-11-16 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_app", "0002_user_history"),
    ]

    operations = [
        migrations.AddField(
            model_name="llmrole",
            name="collaboration_triggers",
            field=models.TextField(
                blank=True,
                help_text="Keywords or patterns that suggest collaboration with this role",
            ),
        ),
        migrations.AddField(
            model_name="llmrole",
            name="collaborators",
            field=models.ManyToManyField(
                blank=True, related_name="can_collaborate_with", to="ai_app.llmrole"
            ),
        ),
    ]