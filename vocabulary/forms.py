from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Card


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Электронная почта")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {"username": "Имя пользователя"}


class CardForm(forms.ModelForm):
    due_at = forms.DateTimeField(input_formats=["%Y-%m-%dT%H:%M"], widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"), label="Следующее повторение")

    class Meta:
        model = Card
        fields = ("word", "translation", "language", "example", "note", "level", "due_at")
        labels = {"word": "Слово или фраза", "translation": "Перевод", "language": "Язык", "example": "Пример употребления", "note": "Заметка", "level": "Уровень", "due_at": "Следующее повторение"}
        widgets = {"example": forms.Textarea(attrs={"rows": 2}), "note": forms.Textarea(attrs={"rows": 2})}
