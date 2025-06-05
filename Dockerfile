FROM python:3.11-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl xvfb \
    libxi6 libgconf-2-4 libnss3 libasound2 libxss1 libatk-bridge2.0-0 \
    libgtk-3-0 libx11-xcb1 fonts-liberation libu2f-udev \
    && rm -rf /var/lib/apt/lists/*

# Установка Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Копируем код
WORKDIR /app
COPY . .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Добавляем ENV-путь к Chrome
ENV CHROME_BINARY=/usr/bin/google-chrome

CMD ["python", "storybot/bot/main.py"]
