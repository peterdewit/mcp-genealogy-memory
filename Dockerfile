FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py /app/server.py
EXPOSE 8020
CMD ["python", "/app/server.py"]
