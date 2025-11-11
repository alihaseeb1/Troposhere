# Dockerfile
FROM python:3.11-slim

# set working dir
WORKDIR /app

# system deps (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# copy requirements first (cache)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# copy application code
COPY . /app

# expose port (uvicorn)
EXPOSE 80

# add an entrypoint script that runs migrations then starts the app
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# NOTE: run with a production ASGI server
CMD ["/app/entrypoint.sh"]