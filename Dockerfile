FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Broad copy kept for reference. It is convenient, but it also includes docs,
# Kubernetes manifests, and other files that are not needed at runtime.
# COPY . .
COPY bot.py .
COPY src ./src

CMD ["python", "bot.py"]
