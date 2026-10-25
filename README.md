# Футбол: данные → результат → сайт

[![Research site](https://github.com/danyaborisoff-collab/python/actions/workflows/site.yml/badge.svg)](https://github.com/danyaborisoff-collab/python/actions/workflows/site.yml)

Задание 3: **T2 + P3**, Python MkDocs + Material. Челлендж с Marketplace не выполняется.
Датасет — минимальный срез пользовательского футбольного архива: GB1, сезоны 2012/13–2024/25.

## Статус

- Эксперимент, проверки, локальная строгая сборка и отчёт подготовлены.
- PR #1 слит в main. GitHub Actions lint/build/deploy прошли: https://github.com/danyaborisoff-collab/python/actions/runs/40208648142
- GitHub Pages опубликован и проверен: HTTP 200 и контрольная строка подтверждены.
  https://danyaborisoff-collab.github.io/python/
- Отечественный хостинг пока не подключён. `.github/workflows/domestic.yml` — настраиваемый SSH workflow, не доказательство доставки.
- Требуется уточнить источник и лицензию исходного датасета перед публичным распространением среза.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make build test
make serve
```

Windows без make: `python scripts/experiment.py`, затем `python -m mkdocs build --strict` и `python -m mkdocs serve`.
Версия Python закреплена в `.python-version`, все зависимости — в `requirements.txt`.

## Проверки и измерения

```bash
make test
make negative
python scripts/demo_update.py
make benchmark
```

`evidence/` содержит реальные локальные логи, замеры и результаты теста обновления.
`docs/` — полный отчёт, `scripts/` — воспроизводимые вычисления и QA.
Первый build не требует Jupyter, pandas, исходного ZIP или внешнего API.

## Публикация

GitHub: Settings → Pages → Source = GitHub Actions. Push/merge в main запускает lint → build → deploy.
Другие ветки и PR только проверяются. Официальный Pages artifact, без push HTML в gh-pages.
Полный workflow и инструкция: `docs/delivery.md`.

Отечественный хостинг: задать `DOMESTIC_SITE_URL`, шесть SSH secrets (см. delivery.md), проверить host fingerprint,
запустить Domestic SSH hosting вручную из main. Пароли/ключи не добавлять в репозиторий.

## Лицензии

Код MIT; текст отчёта CC BY 4.0. Данные имеют отдельные, пока не установленные условия.
Chart.js MIT, лицензия включена. Внешние CDN для отображения сайта не нужны.
