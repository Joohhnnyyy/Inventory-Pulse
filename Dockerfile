# Dockerfile for Inventory Intelligence Tool (IIT) Agent
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY demo/ ./demo/
COPY tests/ ./tests/
COPY .env.example .env

# Create necessary directories
RUN mkdir -p demo/outbox demo/supplier_orders logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default configuration
ENV AUTO_ORDER_THRESHOLD=500.0
ENV VENDOR_TRUST_THRESHOLD=0.8
ENV COMPOSIO_API_KEY=ak_7KV1PgJT2x0XIC_wqejz
ENV WEBHOOK_SECRET=ed999b5c-aea7-44a8-b910-cae4b47cfb46

# Composio project configuration
ENV COMPOSIO_PROJECT_ID=pr_Xc-M1SWXACrp
ENV COMPOSIO_ORG_ID=ok_-vJ1RbVbasXQ
ENV COMPOSIO_ORG_MEMBER_EMAIL=johnsonansh32@gmail.com
ENV COMPOSIO_USER_ID=ff446a18-1872-4af1-a75b-99f52098cf11
ENV COMPOSIO_PLAYGROUND_TEST_USER_ID=pg-test-ff446a18-1872-4af1-a75b-99f52098cf11

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('demo/agent_actions.db'); conn.close()" || exit 1

# Expose port for webhook endpoints (if needed)
EXPOSE 8080

# Default command - run agent in continuous mode
CMD ["python", "-m", "src.agent_main", "--interval", "3600"]

# Alternative commands:
# Run once: docker run iit-agent python -m src.agent_main --run-once
# Dry run: docker run iit-agent python -m src.agent_main --dry-run --run-once
# Custom interval: docker run iit-agent python -m src.agent_main --interval 1800