FROM python:3.10-slim
LABEL "language"="python"
LABEL "framework"="flask"

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "app.py"]
