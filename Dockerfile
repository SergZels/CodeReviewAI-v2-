FROM python:3.11

# Встановлюємо робочу директорію всередині контейнера
WORKDIR /usr/src/app/

# Копіюємо файл requirements.txt і встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо всі файли проекту до робочої директорії контейнера
COPY . .
EXPOSE 7777

# Вказуємо команду для запуску FastAPI додатка
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7777"]