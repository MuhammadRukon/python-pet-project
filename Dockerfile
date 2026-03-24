FROM python:3.12-slim

WORKDIR /dest

COPY requirements.txt .
COPY app ./app

RUN pip install -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]