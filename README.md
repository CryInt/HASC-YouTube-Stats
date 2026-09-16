# YouTube Stats — интеграция для Home Assistant

Кастомный компонент (распространяется через HACS в виде custom repository),
который через **YouTube Data API v3** и **OAuth2** подтягивает данные о
последнем опубликованном видео или Shorts на вашем собственном канале и
показывает их через entity `sensor.<канал>_latest_upload`:

- **Название** — состояние сенсора (title видео)
- **Дата и время публикации** — атрибут `published_at`
- **Количество просмотров** — атрибут `view_count`
- **Количество комментариев** — атрибут `comment_count`
- плюс `content_type` (`video`/`short`), `like_count`, `duration_seconds`,
  `url`, `thumbnail_url`, `description`, `video_id`

Тип контента (`video` или `short`) определяется эвристически по
длительности ролика (≤ 3 минут = Shorts), так как YouTube Data API не
отдаёт официальный флаг Shorts.

Опрашивается только **ваш собственный** канал (через `mine=true`), доступ к
которому даёт OAuth-логин через Google. Обновление данных — раз в 15 минут
(это ~3 квоты YouTube API за опрос, дневная квота по умолчанию — 10 000).

## Как это авторизуется и где хранятся данные

Используется **стандартный механизм Home Assistant** для OAuth2-интеграций
(`config_entry_oauth2_flow` + платформа `application_credentials`, как у
Google Calendar/Nest и других core-интеграций):

- Client ID/Secret вашего Google-проекта регистрируются в HA через
  **Настройки → Устройства и сервисы → Application Credentials** — они
  хранятся в `.storage/application_credentials`.
- После входа через Google токен доступа/обновления сохраняется прямо в
  соответствующей config entry — в `.storage/core.config_entries`, как и у
  любой другой OAuth-интеграции HA. Компонент не создаёт никакого
  собственного хранилища токенов и не хранит секреты в `configuration.yaml`.
- Токен автоматически обновляется Home Assistant при истечении срока
  действия (`async_ensure_token_valid`).

## Установка

### 1. Создать OAuth-клиент в Google Cloud

1. Откройте [Google API Console](https://console.cloud.google.com/apis/credentials)
   и создайте (или выберите) проект.
2. В [библиотеке API](https://console.cloud.google.com/apis/library) включите
   **YouTube Data API v3**.
3. Настройте **OAuth consent screen**:
   - тип User type — External;
   - добавьте scope `.../auth/youtube.readonly`;
   - на вкладке Test users добавьте свой аккаунт Google (пока приложение не
     опубликовано, входить смогут только тестовые пользователи).
4. Создайте **Credentials → OAuth client ID** типа **Web application**.
5. В **Authorized redirect URIs** добавьте:
   - `https://my.home-assistant.io/redirect/oauth` (если используете
     My Home Assistant), и/или
   - `https://<ваш-внешний-url-ha>/auth/external/callback`.
6. Сохраните **Client ID** и **Client Secret**.

### 2. Установить компонент через HACS

1. HACS → три точки в правом верхнем углу → **Custom repositories**.
2. Добавьте URL этого репозитория, категория — **Integration**.
3. Найдите **YouTube Stats** в списке HACS и установите.
4. Перезапустите Home Assistant.

(Пока репозиторий не в основном каталоге HACS, добавление возможно только
как custom repository.)

### 3. Настроить Application Credentials в Home Assistant

**Настройки → Устройства и сервисы → Application Credentials → Добавить
Application Credential**:

- Интеграция: **YouTube Stats**
- Client ID / Client Secret — из шага 1.

### 4. Добавить интеграцию

**Настройки → Устройства и сервисы → Добавить интеграцию → YouTube Stats**,
пройдите вход через Google и разрешите доступ к чтению данных YouTube.
После этого появится устройство с названием вашего канала и сенсор
**Latest upload**.

## Ограничения

- Поддерживается только собственный канал авторизованного аккаунта.
- Различение video/Shorts — эвристика по длительности, а не официальный
  признак API.
- Не рекомендуется уменьшать интервал опроса намного ниже 15 минут — это
  быстрее расходует суточную квоту YouTube Data API.
