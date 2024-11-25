FROM base AS bot
COPY . .
ENV PORT 8080
EXPOSE 8080
CMD ["python3", "bot.py"]