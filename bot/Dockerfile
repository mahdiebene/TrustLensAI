FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot source.
COPY . .

# Unbuffered logs so output streams to docker logs immediately.
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
