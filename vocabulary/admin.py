from django.contrib import admin
from .models import Card, Profile, ReviewLog


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("word", "translation", "owner", "language", "level", "due_at")
    list_filter = ("language", "level")
    search_fields = ("word", "translation", "owner__username")


admin.site.register(Profile)
admin.site.register(ReviewLog)
