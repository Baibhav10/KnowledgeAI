# We use the slim variant to keep the image small —
# it has Python but strips out a lot of OS tools we don't need.
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Install uv for fast dependency installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first (before app code).
# Docker caches each step — if pyproject.toml hasn't changed,
# it skips reinstalling dependencies on the next build. Huge time saver.
COPY pyproject.toml uv.lock ./

# Install dependencies into the system Python (no venv needed in containers)
RUN uv sync --frozen --no-dev

# Now copy the rest of the application code
COPY . .

# Expose the port uvicorn will run on
EXPOSE 8000

# Start the server
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]