FROM python:3.11-slim

# system deps
RUN apt-get update && apt-get install -y \
    wget gnupg ca-certificates  && \
    rm -rf /var/lib/apt/lists/*

# poetry / requirements
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "-m", "bot.main"]
