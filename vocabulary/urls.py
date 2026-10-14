from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cards/", views.cards, name="cards"),
    path("cards/new/", views.card_create, name="card_create"),
    path("cards/<int:pk>/edit/", views.card_edit, name="card_edit"),
    path("cards/<int:pk>/delete/", views.card_delete, name="card_delete"),
    path("review/", views.review, name="review"),
    path("review/<int:pk>/answer/", views.review_answer, name="review_answer"),
    path("progress/", views.progress, name="progress"),
    path("audio/", views.audio, name="audio"),
    path("telegram/webhook/", views.telegram_webhook, name="telegram_webhook"),
    path("telegram/link/", views.telegram_link, name="telegram_link"),
]
