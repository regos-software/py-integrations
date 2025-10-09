# TsdIntegration

Интеграция с системой Regos для работы с документами закупок и PWA-интерфейсом.

## Основное

- Класс: `TsdIntegration(ClientBase)`
- Ключ интеграции: `"tsd"`
- PWA (React) код: `clients/tsd/pwa/src/*`
- Собранные фронтовые ассеты: `clients/tsd/pwa/assets/app.js`, `clients/tsd/pwa/assets/app.css`
- Кэш настроек в Redis (`SETTINGS_TTL`)

## Основные методы

### handle_external(data)

Обработка внешних запросов (обычно POST).  
Поддерживаемые `action`:

- `ping`, `login`, `send`
- `purchase_list` — список документов
- `purchase_get` — документ и операции
- `purchase_ops_get` / `add` / `edit` / `delete`
- `product_search` — поиск номенклатуры

Возвращает JSON-ответ.

### handle_ui(envelope)

Обработка GET-запросов для PWA:

- `?asset=` — выдача статических файлов
- `?pwa=sw` — service worker
- `?pwa=manifest` — web manifest
- по умолчанию — `index.html` с внедрением `window.__CI__`

## Frontend (React) Workflow

PWA переписана на React и собирается через `esbuild` в единый модуль `assets/app.js`, совместимый с текущим серверным роутингом (`?assets=app.js`).

### Установка зависимостей

```powershell
cd clients/tsd/pwa
npm install
```

### Сборка

```powershell
npm run build
```

Скрипт создаст/обновит `assets/app.js` (ESM) c картой исходников. Глобальные стили остаются в `assets/app.css`.

### Режим разработки

Запустите вотчер, который будет пересобирать `assets/app.js` при изменениях.

```powershell
npm run dev
```

Для локального предпросмотра можно использовать `npm run serve` (использует `live-server`).

## Вспомогательные методы

- `_safe_join(base, rel)` — безопасное объединение путей
- `_json_error(status, desc)` — JSON-ошибка
- `_fetch_settings(cache_key)` — загрузка и кэширование настроек

## Пример

```python
integration = TsdIntegration(connected_integration_id="abc123")

response = await integration.handle_external({
    "method": "POST",
    "headers": {"Connected-Integration-Id": "abc123"},
    "body": {"action": "purchase_list", "params": {"page": 1, "page_size": 10}}
})
```
