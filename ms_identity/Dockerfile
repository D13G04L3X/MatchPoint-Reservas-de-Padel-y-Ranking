FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir setuptools==70.3.0

COPY . /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
