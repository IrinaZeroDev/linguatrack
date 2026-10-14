from datetime import timedelta
from django.utils import timezone


def schedule_review(card, quality):
    """SM-2 review update. quality is an integer from 0 (forgot) to 5 (easy)."""
    quality = max(0, min(5, int(quality)))
    if quality < 3:
        card.repetitions = 0
        card.interval = 1
    else:
        if card.repetitions == 0:
            card.interval = 1
        elif card.repetitions == 1:
            card.interval = 6
        else:
            card.interval = max(1, round(card.interval * card.ease))
        card.repetitions += 1
        card.ease = max(1.3, card.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    card.due_at = timezone.now() + timedelta(days=card.interval)
    card.last_reviewed = timezone.now()
    card.save(update_fields=["repetitions", "interval", "ease", "due_at", "last_reviewed"])
    return card
