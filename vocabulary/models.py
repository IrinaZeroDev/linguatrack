from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True)
    link_code = models.CharField(max_length=40, blank=True)
    test_card = models.ForeignKey("Card", null=True, blank=True, on_delete=models.SET_NULL, related_name="telegram_tests")

    def __str__(self):
        return f"Профиль {self.user.username}"


class Card(models.Model):
    LEVELS = [("beginner", "Начальный"), ("intermediate", "Средний"), ("advanced", "Продвинутый")]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cards")
    word = models.CharField(max_length=120)
    translation = models.CharField(max_length=180)
    example = models.CharField(max_length=300, blank=True)
    note = models.CharField(max_length=300, blank=True)
    language = models.CharField(max_length=32, default="Английский")
    level = models.CharField(max_length=16, choices=LEVELS, default="beginner")
    interval = models.PositiveIntegerField(default=0)
    ease = models.FloatField(default=2.5)
    repetitions = models.PositiveIntegerField(default=0)
    due_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    last_reviewed = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["due_at", "word"]

    def __str__(self):
        return f"{self.word} — {self.translation}"

    @property
    def is_due(self):
        return self.due_at <= timezone.now()


class ReviewLog(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="review_logs")
    quality = models.PositiveSmallIntegerField()
    reviewed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-reviewed_at"]
