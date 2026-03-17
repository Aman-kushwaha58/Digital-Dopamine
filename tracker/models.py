from django.db import models

class UserActivity(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    active_app = models.CharField(max_length=255)
    typing_speed = models.IntegerField(default=0)
    app_switch_count = models.IntegerField(default=0)
    dopamine_score = models.IntegerField(default=0)

    STATUS_CHOICES = [
        ('Focused', 'Focused'),
        ('Distracted', 'Distracted'),
        ('Doomscrolling', 'Doomscrolling'),
        ('Neutral', 'Neutral'),
        ('High Dopamine Risk', 'High Dopamine Risk'),
        ('Deep Focus Session', 'Deep Focus Session'),
        ('DOPAMINE SPIKE DETECTED', 'DOPAMINE SPIKE DETECTED'),
    ]

    status = models.CharField(
        max_length=100,
        choices=STATUS_CHOICES,
        default='Neutral'
    )

    def __str__(self):
        return f"{self.active_app} - {self.status}"
