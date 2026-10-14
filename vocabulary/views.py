import json
import os
import secrets
import urllib.parse
import urllib.request
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .forms import CardForm, SignUpForm
from .models import Card, Profile, ReviewLog
from .services import schedule_review


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Profile.objects.get_or_create(user=user)
        login(request, user)
        return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    error = None
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user:
            login(request, user)
            return redirect(request.GET.get("next") or "dashboard")
        error = "Проверьте имя пользователя и пароль."
    return render(request, "registration/login.html", {"error": error})


def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    cards = Card.objects.filter(owner=request.user)
    due_cards = cards.filter(due_at__lte=timezone.now())
    reviewed_today = ReviewLog.objects.filter(owner=request.user, reviewed_at__date=timezone.localdate()).count()
    learned = cards.filter(repetitions__gte=3).count()
    recent = cards.order_by("-created_at")[:5]
    return render(request, "vocabulary/dashboard.html", {"total": cards.count(), "due": due_cards.count(), "learned": learned, "reviewed_today": reviewed_today, "recent": recent})


@login_required
def cards(request):
    qs = Card.objects.filter(owner=request.user)
    level = request.GET.get("level", "")
    language = request.GET.get("language", "")
    search = request.GET.get("q", "").strip()
    if level:
        qs = qs.filter(level=level)
    if language:
        qs = qs.filter(language=language)
    if search:
        qs = qs.filter(word__icontains=search) | qs.filter(translation__icontains=search)
    return render(request, "vocabulary/cards.html", {"cards": qs, "levels": Card.LEVELS, "selected_level": level, "selected_language": language, "languages": Card.objects.filter(owner=request.user).values_list("language", flat=True).distinct(), "q": search})


@login_required
def card_create(request):
    form = CardForm(request.POST or None, initial={"due_at": timezone.localtime()})
    if request.method == "POST" and form.is_valid():
        card = form.save(commit=False)
        card.owner = request.user
        card.save()
        messages.success(request, f"Карточка «{card.word}» добавлена в словарь.")
        return redirect("cards")
    return render(request, "vocabulary/card_form.html", {"form": form, "title": "Новая карточка"})


@login_required
def card_edit(request, pk):
    card = get_object_or_404(Card, pk=pk, owner=request.user)
    form = CardForm(request.POST or None, instance=card)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Изменения сохранены.")
        return redirect("cards")
    return render(request, "vocabulary/card_form.html", {"form": form, "title": "Редактировать карточку"})


@login_required
def card_delete(request, pk):
    card = get_object_or_404(Card, pk=pk, owner=request.user)
    if request.method == "POST":
        card.delete()
        messages.success(request, "Карточка удалена.")
    return redirect("cards")


@login_required
def review(request):
    qs = Card.objects.filter(owner=request.user)
    card = qs.filter(due_at__lte=timezone.now()).first()
    remaining = qs.filter(due_at__lte=timezone.now()).count()
    return render(request, "vocabulary/review.html", {"card": card, "remaining": remaining, "total": qs.count()})


@login_required
def review_answer(request, pk):
    if request.method != "POST":
        return redirect("review")
    card = get_object_or_404(Card, pk=pk, owner=request.user)
    try:
        quality = int(request.POST.get("quality", 0))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Оценка должна быть от 0 до 5"}, status=400)
    if quality not in range(6):
        return JsonResponse({"error": "Оценка должна быть от 0 до 5"}, status=400)
    schedule_review(card, quality)
    ReviewLog.objects.create(owner=request.user, card=card, quality=quality)
    messages.success(request, "Ответ сохранён — расписание повторений обновлено.")
    return redirect("review")


@login_required
def progress(request):
    qs = Card.objects.filter(owner=request.user)
    logs = ReviewLog.objects.filter(owner=request.user)
    today = timezone.localdate()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    activity = [{"label": day.strftime("%a"), "count": logs.filter(reviewed_at__date=day).count()} for day in days]
    level_counts = qs.values("level").annotate(count=Count("id"))
    return render(request, "vocabulary/progress.html", {"total": qs.count(), "learned": qs.filter(repetitions__gte=3).count(), "due": qs.filter(due_at__lte=timezone.now()).count(), "reviews": logs.count(), "activity": activity, "max_activity": max([x["count"] for x in activity] + [1]), "level_counts": level_counts, "accuracy": round(logs.filter(quality__gte=3).count() / logs.count() * 100) if logs.exists() else 0})


def audio(request):
    text = request.GET.get("text", "").strip()[:180]
    if not text:
        return JsonResponse({"error": "Введите слово для озвучивания"}, status=400)
    return JsonResponse({"text": text, "mode": "browser", "message": "Используется встроенная озвучка браузера"})


def _telegram_send(chat_id, text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    try:
        urllib.request.urlopen(req, timeout=5).read()
    except Exception:
        pass


def _telegram_send_voice(chat_id, text, language="en"):
    """Create short speech with gTTS and deliver it as a Telegram voice message."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return False
    try:
        from gtts import gTTS
        from io import BytesIO
        lang = language.lower()
        lang_code = "fr" if "фран" in lang or "fran" in lang else "de" if "нем" in lang or "german" in lang else "es" if "исп" in lang or "span" in lang else "it" if "итал" in lang or "ital" in lang else "en"
        audio = BytesIO()
        gTTS(text=text, lang=lang_code).write_to_fp(audio)
        boundary = "----LinguaTrackVoiceBoundary"
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n"
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"voice\"; filename=\"word.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n").encode() + audio.getvalue() + f"\r\n--{boundary}--\r\n".encode()
        request = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendVoice", data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        urllib.request.urlopen(request, timeout=15).read()
        return True
    except Exception:
        return False


@csrf_exempt
def telegram_webhook(request):
    if request.method != "POST":
        return HttpResponse("OK")
    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
    if not secret or request.headers.get("X-Telegram-Bot-Api-Secret-Token") != secret:
        return HttpResponseForbidden()
    try:
        update = json.loads(request.body)
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").strip()
        if not chat_id or not text:
            return JsonResponse({"ok": True})
        command, _, argument = text.partition(" ")
        if command == "/start":
            if argument.startswith("link_"):
                code = argument[5:]
                profile = Profile.objects.filter(link_code=code).select_related("user").first()
                if profile:
                    profile.telegram_id = chat_id
                    profile.link_code = ""
                    profile.save(update_fields=["telegram_id", "link_code"])
                    answer = f"Готово, {profile.user.username}! Telegram подключён. Команды: /today, /test, /progress, /cards, /say слово"
                else:
                    answer = "Ссылка устарела. Создайте новую в настройках LinguaTrack."
            else:
                answer = "Привет! Подключите аккаунт через кнопку Telegram в LinguaTrack, затем используйте /today, /test, /progress, /cards и /say слово."
        else:
            profile = Profile.objects.filter(telegram_id=chat_id).select_related("user").first()
            if not profile:
                answer = "Сначала подключите аккаунт: откройте LinguaTrack → Прогресс → Telegram."
            else:
                qs = Card.objects.filter(owner=profile.user)
                due = qs.filter(due_at__lte=timezone.now())
                if command == "/today":
                    answer = "На сегодня:\n" + ("\n".join(f"• {c.word} — {c.translation}" for c in due[:10]) if due.exists() else "Повторений пока нет. Отличная работа!")
                elif command == "/cards":
                    answer = "Ваши карточки:\n" + ("\n".join(f"• {c.word} — {c.translation}" for c in qs[:15]) if qs.exists() else "Словарь пока пуст.")
                elif command == "/progress":
                    answer = f"Прогресс LinguaTrack\nСлов в словаре: {qs.count()}\nВыучено: {qs.filter(repetitions__gte=3).count()}\nНа сегодня: {due.count()}\nПовторений всего: {ReviewLog.objects.filter(owner=profile.user).count()}"
                elif command == "/say" and argument:
                    card = qs.filter(word__iexact=argument).first()
                    voiced = _telegram_send_voice(chat_id, argument, card.language if card else "en")
                    answer = f"🔊 {argument}" if voiced else f"Не удалось создать аудио. Слово: {argument}"
                elif command == "/test":
                    card = due.first() or qs.first()
                    if card:
                        profile.test_card = card
                        profile.save(update_fields=["test_card"])
                        answer = f"Переведите слово: {card.word}\nНапишите перевод ответным сообщением."
                    else:
                        answer = "Сначала добавьте несколько карточек в словарь."
                elif not command.startswith("/") and profile.test_card_id:
                    card = profile.test_card
                    correct = text.casefold().strip() == card.translation.casefold().strip()
                    quality = 4 if correct else 1
                    schedule_review(card, quality)
                    ReviewLog.objects.create(owner=profile.user, card=card, quality=quality)
                    profile.test_card = None
                    profile.save(update_fields=["test_card"])
                    answer = f"✅ Верно! {card.word} — {card.translation}." if correct else f"Пока не совсем. Правильный ответ: {card.translation}. Добавил слово в повторение."
                else:
                    answer = "Доступны: /today, /test, /progress, /say слово, /cards"
        _telegram_send(chat_id, answer)
        return JsonResponse({"ok": True})
    except (ValueError, TypeError, KeyError):
        return JsonResponse({"ok": False}, status=400)


@login_required
def telegram_link(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        profile.link_code = secrets.token_urlsafe(12)
        profile.save(update_fields=["link_code"])
        username = os.environ.get("TELEGRAM_BOT_USERNAME", "")
        return JsonResponse({"url": f"https://t.me/{username}?start=link_{profile.link_code}" if username else "", "username": username})
    return JsonResponse({"connected": bool(profile.telegram_id)})
