FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .

FROM base AS bot
CMD ["python3", "bot.py"]

FROM base AS fastapi
CMD ["uvicorn", "model_api:app", "--host", "0.0.0.0", "--port", "8080"]