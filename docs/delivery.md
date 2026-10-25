# Сборка, CI/CD и размещение

## Выполненные и подготовленные шаги

| Шаг | Реализация / состояние |
| --- | --- |
| Python и pip | Проверены локально; точная версия приведена в измерениях |
| Виртуальное окружение | Создано через `python -m venv`; virtualenv дополнительно установлен и закреплён |
| Фиксация зависимостей | Полный `requirements.txt`, `.python-version`, `.gitignore` |
| Генератор | MkDocs 1.6.1 + Material 9.6.23 |
| Локальный preview | `make serve` / `python -m mkdocs serve` |
| Строгая сборка | `make build`, `strict: true`, диагностика ссылок настроена как warnings |
| Репозиторий | [danyaborisoff-collab/python](https://github.com/danyaborisoff-collab/python); первоначальный 403 устранён переподключением; создана ветка research-site-t2-p3 |
| GitHub Actions | Конфигурация подготовлена; удалённый запуск не подтверждён |
| GitHub Pages | Нужно выбрать Source = GitHub Actions и выполнить merge/push в main |
| Отечественный хостинг | SSH workflow подготовлен, аккаунт/путь ещё не предоставлены |
| URL и подкаталог | `use_directory_urls: false`, относительные ссылки; канонический URL через MKDOCS_SITE_URL |
| Контроль качества | Валидация CSV, независимый пересчёт, ссылки/якоря, HTTP marker, поиск, локальные ресурсы |
| Лицензии | MIT для кода, CC BY 4.0 для авторского текста; данные отдельно |

## Локальное воспроизведение

```bash
python --version
python -m pip --version
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m virtualenv --version
make build test
make serve
```

Если `make` отсутствует, последовательность эквивалентна:

```bash
python scripts/experiment.py
python -m unittest discover -s tests -v
python scripts/verify_results.py
python -m mkdocs build --strict
python scripts/check_site.py site
python -m mkdocs serve
```

## GitHub Actions

Конфигурация: `.github/workflows/site.yml`.

```text
push любой ветки / pull_request / workflow_dispatch
  lint: CSV, unit tests, независимый пересчёт, mkdocs --strict, ссылки
    └── build: pip cache, experiment cache, site/ → research-site artifact
          └── только main и не pull_request:
               github-pages artifact → deploy-pages → HTTP healthcheck
```

| Событие | lint/build | deploy |
| --- | --- | --- |
| push main | Да | Да |
| push другой ветки | Да | Нет |
| pull_request | Да, без обычных deploy-секретов | Нет |
| workflow_dispatch на main | Да | Да |
| workflow_dispatch на другой ветке | Да | Нет |
| push тега | Не настроен | Нет |

Дублирование push и PR-проверок для ветки с открытым PR возможно и намеренно не скрывается.
Все сторонние actions закреплены полными SHA, а не подвижными тегами.
`persist-credentials: false` не оставляет checkout credential для последующих команд.
Права `pages:write` и `id-token:write` выдаются только job deploy.

### Как включить публикацию

1. Загрузить проект в репозиторий с сохранением `.github/workflows/`.
2. Открыть **Settings → Pages → Build and deployment → Source → GitHub Actions**.
3. Выполнить push/merge в `main` или запустить `Research site` вручную на main.
4. Проверить все job и фактический URL в environment github-pages.
5. Ожидаемый адрес: `https://danyaborisoff-collab.github.io/python/`.
   Пока deploy не прошёл, это только ожидаемый адрес, не подтверждение опубликованного сайта.

Официальный путь и настройки описаны в
[Publishing with a custom GitHub Actions workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

### Два подхода к Pages

| Подход | Механизм | Отличие |
| --- | --- | --- |
| Push в gh-pages | Например, peaceiris/actions-gh-pages записывает HTML в ветку | Нужны права записи содержимого; результат хранится в Git и Pages настраивают на эту ветку |
| Официальный artifact + deploy | upload-pages-artifact + deploy-pages | Нет коммитов с HTML; `pages:write`, OIDC и environment; Source = GitHub Actions |

В работе выбран второй вариант. Нельзя одновременно ожидать публикацию ветки gh-pages
и использовать настройки Source = Actions без понимания разных моделей.

## Отечественный SSH-хостинг

`.github/workflows/domestic.yml` — отдельный ручной workflow **Domestic SSH hosting**.
Перед подключением необходимо уточнить у администратора Helios или другого сервиса:
адрес/порт SSH, доступность rsync, абсолютный каталог публикации, веб-URL,
права на каталог и fingerprint host key. Путь `public_html` не угадывается автоматически.

Repository variable:

| Имя | Значение |
| --- | --- |
| DOMESTIC_SITE_URL | Полный опубликованный URL со схемой HTTPS и завершающим `/` |

Repository/environment secrets:

| Имя | Назначение |
| --- | --- |
| DEPLOY_HOST | SSH-хост |
| DEPLOY_PORT | SSH-порт |
| DEPLOY_USER | Выделенный пользователь |
| DEPLOY_PATH | Абсолютный выделенный каталог сайта |
| DEPLOY_SSH_KEY | Закрытый отдельный deploy-ключ |
| DEPLOY_KNOWN_HOSTS | Проверенная строка known_hosts; для нестандартного порта — [host]:port |

Ключ выдаётся только для нужного каталога/пользователя, не для всего сервера.
Fingerprint сверяется по независимому каналу с администратором; не используется `StrictHostKeyChecking=no`.
Секреты не печатаются, `set -x` не включён. Маскирование в реальном CI **ещё не проверено**.

Публикация вызывается вручную из main; workflow повторно собирает сайт для целевого site_url,
передаёт файлы по rsync и проверяет HTTP 200 и `RESEARCH-SITE-OK`.
`--delete` отключён для безопасности. `--delay-updates` уменьшает окно частично обновлённых отдельных файлов,
но не обеспечивает атомарность всего сайта, rollback и preview-ветки (P4 не выбрано).
При обрыве возможна смесь старых/новых файлов: повторить доставку; для production-атомарности нужны release directories и переключение симлинка с учётом правил хостинга.

## Подкаталог и автономность

Для другого адреса:

```bash
MKDOCS_SITE_URL='https://example.ru/~user/research/' make build
```

Это шаблон команды, не настоящий URL пользователя.
Относительные `.html`-ссылки и ссылки на assets сохраняют работоспособность в подкаталоге.
Google Fonts отключены (`font: false`), Chart.js 4.4.1 хранится локально с MIT license,
иконки темы встроены, формула — MathML. Частичный override `partials/source.html` отключает необязательный запрос статистики GitHub API, оставляя обычную ссылку на репозиторий. Внешние гиперссылки на источники не являются зависимостями отображения.
Поиск локальный, языки ru и en; полноценная семантическая морфология не обещается.

## Доказательства после удалённого запуска

Нужно сохранить URL успешного workflow, скриншот lint/build/deploy и намеренно проваленного запуска,
фактические URL двух хостингов, HTTP-логи и замеры доставки.
Сейчас такие доказательства не заменяются локальными скриншотами или вымышленными ссылками.

## Полный workflow GitHub Pages

```yaml
name: Research site
on:
  push:
    branches: ['**']
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: site-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  lint:
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
        with:
          persist-credentials: false
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
        with:
          python-version-file: .python-version
          cache: pip
          cache-dependency-path: requirements.txt
      - run: python -m pip install -r requirements.txt
      - name: Validate data, calculations and strict links
        run: |
          make experiment test
          python -m mkdocs build --strict --site-dir .lint-site
          python scripts/check_site.py .lint-site
  build:
    needs: lint
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
        with:
          persist-credentials: false
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
        with:
          python-version-file: .python-version
          cache: pip
          cache-dependency-path: requirements.txt
      - run: python -m pip install -r requirements.txt
      - uses: actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830 # v4
        with:
          path: .cache/experiment
          key: experiment-${{ runner.os }}-${{ hashFiles('.python-version', 'requirements.txt', 'scripts/experiment.py', 'data/*.csv', 'data/manifest.json') }}
      - name: Build once and independently verify
        run: make build verify
      - name: Store regular build artifact for inspection
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
        with:
          name: research-site
          path: site/
          retention-days: 7
      - name: Package official Pages artifact (only main)
        if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'
        uses: actions/upload-pages-artifact@56afc609e74202658d3ffba0e8f6dda462b719fa # v3
        with:
          path: site/
  deploy:
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    permissions:
      contents: read
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/configure-pages@983d7736d9b0ae728b81ab479565c72886d7745b # v5
      - id: deployment
        uses: actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e # v4
      - name: Check HTTP status and control marker
        env:
          SITE_URL: ${{ steps.deployment.outputs.page_url }}
        run: |
          for attempt in $(seq 1 12); do
            status=$(curl --silent --show-error --location --output /tmp/page.html --write-out '%{http_code}' "${SITE_URL}")
            if [ "$status" = '200' ] && grep -q 'RESEARCH-SITE-OK' /tmp/page.html; then
              echo 'Healthcheck passed'; exit 0
            fi
            sleep 5
          done
          echo 'Healthcheck failed: HTTP status or marker mismatch' >&2
          exit 1
```

## Полный workflow SSH-хостинга

```yaml
# Шаблон для Helios или другого российского SSH-хостинга. До добавления
# секретов/подтверждения доступа НЕ считается выполненным развёртыванием.
name: Domestic SSH hosting
on:
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: domestic-production
  cancel-in-progress: false
jobs:
  build:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
        with:
          persist-credentials: false
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065 # v5
        with:
          python-version-file: .python-version
          cache: pip
          cache-dependency-path: requirements.txt
      - run: python -m pip install -r requirements.txt
      - name: Build for domestic URL
        env:
          MKDOCS_SITE_URL: ${{ vars.DOMESTIC_SITE_URL }}
        run: |
          test -n "$MKDOCS_SITE_URL" || { echo 'Set DOMESTIC_SITE_URL repository variable'; exit 1; }
          make build test
      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
        with:
          name: domestic-site
          path: site/
          retention-days: 7
  deploy:
    needs: build
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    environment: domestic-production
    steps:
      - uses: actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093 # v4
        with:
          name: domestic-site
          path: site
      - name: Deploy with a dedicated SSH key and pinned host identity
        env:
          SSH_KEY: ${{ secrets.DEPLOY_SSH_KEY }}
          KNOWN_HOSTS: ${{ secrets.DEPLOY_KNOWN_HOSTS }}
          DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
          DEPLOY_USER: ${{ secrets.DEPLOY_USER }}
          DEPLOY_PORT: ${{ secrets.DEPLOY_PORT }}
          DEPLOY_PATH: ${{ secrets.DEPLOY_PATH }}
          SITE_URL: ${{ vars.DOMESTIC_SITE_URL }}
        shell: bash
        run: |
          set -euo pipefail
          # Не включать set -x и не печатать значения секретов.
          for var in SSH_KEY KNOWN_HOSTS DEPLOY_HOST DEPLOY_USER DEPLOY_PORT DEPLOY_PATH SITE_URL; do
            test -n "${!var}" || { echo "Missing configuration: $var"; exit 1; }
          done
          [[ "$DEPLOY_HOST" =~ ^[a-zA-Z0-9.-]+$ ]]
          [[ "$DEPLOY_USER" =~ ^[a-zA-Z0-9_-]+$ ]]
          [[ "$DEPLOY_PORT" =~ ^[0-9]+$ ]]
          # Только безопасный абсолютный путь к ВЫДЕЛЕННОМУ каталогу сайта.
          [[ "$DEPLOY_PATH" =~ ^/[a-zA-Z0-9_./-]+$ ]]
          [[ "$DEPLOY_PATH" != '/' && "$DEPLOY_PATH" != *'..'* ]]
          key=$(mktemp); hosts=$(mktemp)
          trap 'rm -f "$key" "$hosts"' EXIT
          chmod 600 "$key" "$hosts"
          printf '%s\n' "$SSH_KEY" > "$key"
          printf '%s\n' "$KNOWN_HOSTS" > "$hosts"
          # Fingerprint заранее сверяется с администратором; ssh-keyscan сам
          # по себе не доказывает подлинность хоста.
          export RSYNC_RSH="ssh -i $key -p $DEPLOY_PORT -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$hosts"
          rsync -az --delay-updates site/ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/"
          # --delete намеренно НЕ используется: чужие файлы не удаляются.
          for attempt in $(seq 1 6); do
            code=$(curl -sS -L -o /tmp/domestic.html -w '%{http_code}' "$SITE_URL")
            if [ "$code" = '200' ] && grep -q 'RESEARCH-SITE-OK' /tmp/domestic.html; then
              echo 'Domestic healthcheck passed'; exit 0
            fi
            sleep 5
          done
          echo 'Domestic healthcheck failed' >&2; exit 1
```
