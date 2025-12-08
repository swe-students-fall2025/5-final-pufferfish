FROM python:3.11-slim

# Install ca-certificates for SSL
RUN apt-get update && apt-get install -y \
    ca-certificates \
    openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]

# production
CMD ["python", "app.py"]