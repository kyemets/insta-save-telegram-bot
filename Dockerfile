FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl xvfb \
    libxi6 libnss3 libasound2 libxss1 libatk-bridge2.0-0 \
    libgtk-3-0 libx11-xcb1 fonts-liberation libu2f-udev \
 && wget -q -O /etc/apt/trusted.gpg.d/google-linux.gpg https://dl.google.com/linux/linux_signing_key.pub \
 && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update && apt-get install -y google-chrome-stable \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV CHROME_BINARY=/usr/bin/google-chrome

CMD ["python", "-m", "storybot.bot.main"]
