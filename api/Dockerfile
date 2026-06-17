# Base image: Python 3.11 "slim" variant (lighter, no packages we don't need)
FROM python:3.11-slim

# Working directory inside the container -- everything below is relative to this.
WORKDIR /app

# Copy ONLY requirements.txt first (not all the code yet) and install it.
# This is a caching trick: if you later change app code but not dependencies,
# Docker reuses this already-installed layer instead of reinstalling from scratch.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application code.
COPY app/ ./app/

# Documents that the container listens on port 8000 (informational, doesn't open it by itself).
EXPOSE 8000

# Command that runs when the container starts.
# --host 0.0.0.0 is required: it means "accept connections from outside the container",
# not just from localhost inside it.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
