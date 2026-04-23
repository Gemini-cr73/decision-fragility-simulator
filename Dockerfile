# Use a slim Python base image
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway uses PORT=8080
ENV PORT=8080
ENV STREAMLIT_SERVER_PORT=8080

EXPOSE 8080

CMD ["streamlit", "run", "app/ui/streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0"]
