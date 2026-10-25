# С чего начать

Внутри готовый локально проверенный проект задания 3: T2 + P3 на вашем футбольном датасете.
Челлендж с Marketplace не выполнялся.

1. Откройте README.md и docs/delivery.md.
2. Установите Python версии из .python-version, создайте .venv и выполните pip install -r requirements.txt.
3. Запустите python scripts/experiment.py, затем python -m mkdocs serve.
4. Для GitHub загрузите файлы проекта в корень python (включая скрытый каталог .github).
5. Выберите Settings → Pages → Source = GitHub Actions и выполните push/merge в main.
6. Дождитесь lint/build/deploy. Только после этого ссылка Pages становится подтверждённым результатом.
7. Для отечественного хостинга нужны SSH-доступ, отдельный deploy-ключ, проверенный host key, каталог и публичный URL.

GitHub-часть уже выполнена: PR #1 слит в main, lint/build/deploy успешны, сайт https://danyaborisoff-collab.github.io/python/ отвечает HTTP 200.
Что ещё не выполнено: SSH deploy, удалённая демонстрация изменения CSV→обновлённый график, screenshots удалённых workflow.
Не выдавайте локальные доказательства за эти шаги.

Лицензия пользовательского датасета не указана: перед публичным распространением CSV уточните первоисточник и условия.
Исходный ZIP, окружение Python, кэш и секреты в этот пакет не включаются.

Исходный архив проекта предназначен для Git; отдельный site.zip содержит уже собранный HTML для хостинга.
Открывать поиск корректнее через HTTP (mkdocs serve или python -m http.server), а не через file://.
