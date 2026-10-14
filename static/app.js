document.addEventListener('click', (event) => {
  const reveal = event.target.closest('.reveal-btn');
  if (reveal) {
    const area = reveal.closest('[data-answer]');
    area.classList.add('revealed');
    reveal.remove();
  }
  const sound = event.target.closest('[data-speak]');
  if (sound && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const phrase = new SpeechSynthesisUtterance(sound.dataset.speak);
    const lang = (sound.dataset.lang || '').toLowerCase();
    phrase.lang = lang.includes('fr') || lang.includes('фран') ? 'fr-FR' : lang.includes('de') || lang.includes('нем') ? 'de-DE' : lang.includes('es') || lang.includes('исп') ? 'es-ES' : lang.includes('it') || lang.includes('итал') ? 'it-IT' : 'en-US';
    window.speechSynthesis.speak(phrase);
    sound.classList.add('speaking');
    phrase.onend = () => sound.classList.remove('speaking');
  }
});

document.querySelector('#connectTelegram')?.addEventListener('click', async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    const response = await fetch('/telegram/link/', {method: 'POST', headers: {'X-CSRFToken': document.cookie.split('; ').find(x => x.startsWith('csrftoken='))?.split('=')[1] || ''}});
    const data = await response.json();
    const result = document.querySelector('#telegramLink');
    result.innerHTML = data.url ? `<a href="${data.url}">Открыть Telegram и подключить →</a>` : 'Укажите TELEGRAM_BOT_USERNAME в настройках приложения.';
  } catch { document.querySelector('#telegramLink').textContent = 'Не удалось создать ссылку. Попробуйте позже.'; }
  button.disabled = false;
});
