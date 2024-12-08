## Обработка ошибок

Были обработаны следующие типы ошибок:

### 1. Пустые поля ввода
Если пользователь оставляет хотя бы одно поле пустым, система не начинает работу и сразу выводит блажку заполните поле.

#### Влияние:
- Пользователю сразу приходит оповещение ввести город, оршибка не допускается.

---

### 2. Город не найден
Пользователь вводит неправильное название города или такого города нет в базе.
`City '<город>' not found.`

#### Влияние:
- Система сообщит, что город не найден, и пользователь введет по-другому.
---

### 3. Ошибки API
Если AccuWeather API недоступен, или ключ превысил лимиты:
`Network error or API unavailable.`

**Влияние:**
- Сообщаем пользователю, что API недоступен сейчас. Он вернется позже или подождет.

---

### 4. Неизвестные ошибки
Если возникает непредвиденная ошибка в коде, система выводит сообщение:
`An unexpected error occurred.`

**Влияние:**
- Пользователь получает понятное сообщение о проблеме. Система не падает и остается в рабочем состоянии.

---

## Как обработка ошибок влияет на работоспособность системы

- Все ошибки обрабатываются с помощью `try-except`, что не дает приложению прерываться.
- Сообщения об ошибках выводятся понятно, красиво и заметно. А пр отсутствии ввода всплывает предупреждение.
- Приложение стабильно и вызывает доверия при любых действиях со стороны пользователя.

---

## Проверка работоспособности (можете сами повводить)

### Пример 1: Пустые поля ввода
Оставить поля ввода пустыми.

**Результат:** всплывет блажка заполните поле.
### Пример 2: Неверный город
Ввести неправильное/несуществующее название города (например, `Mcow`).

**Результат:** сообщение об ошибке c отображением названия, чтобы пользователь заметил ошибку `City 'Mcow' not found.`
### Пример 3: Ошибка API
Отключить интернет или использовать неправильный API-ключ.

**Результат:** сообщение об ошибке `Network error or API unavailable.`

### Пример 4: Непредвиденная ошибка
Ввести неверные данные в коде.

**Результат:** сообщение об ошибке `An unexpected error occurred.`

---


Система довольно стабильно работает в любых условиях и всячески противится жесткому ограничению на кючи и созданию новых почт.
