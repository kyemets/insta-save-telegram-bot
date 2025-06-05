FROM python:3.11

WORKDIR /storybot/bot
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "-m", "storybot.bot.main"]
