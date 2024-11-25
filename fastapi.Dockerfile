FROM base AS fastapi
COPY . .
ENV PORT 8080
EXPOSE 8080
CMD ["uvicorn", "model_api:app", "--host", "0.0.0.0", "--port", "8080"]