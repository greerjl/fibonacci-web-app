# Build the Python container
FROM python:3.13-slim

# disable Python bytecode generation and enable unbuffered output 
# --> containers stay immutable and logs are emitted immediately for K8s logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Non-root for better container hygiene
RUN useradd -m appuser

WORKDIR /app

# Install runtime deps separately to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

USER appuser

EXPOSE 8000

CMD ["python", "main.py"]
