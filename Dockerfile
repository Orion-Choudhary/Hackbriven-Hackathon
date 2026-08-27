FROM python:3.11-slim

# Prevent Python from writing bytecode and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

# Install project dependencies
COPY infraguard/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy full repository source code
COPY . .

# Expose default application port
EXPOSE 8000

# Run Commander Agent entrypoint
CMD ["python", "-m", "infraguard.agents.commander.main"]
