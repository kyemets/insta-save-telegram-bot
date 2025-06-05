FROM python:3.11

RUN apt-get update && apt-get install -y chromium

ENV CHROME_BINARY=/usr/bin/chromium

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "storybot.bot.main"]
