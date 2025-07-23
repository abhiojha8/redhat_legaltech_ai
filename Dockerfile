# Multi-stage build for LegalTech AI with RAG and TRAI compliance
FROM registry.access.redhat.com/ubi9/python-311:latest AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for ChromaDB and ML libraries
USER root
RUN dnf update -y && \
    dnf install -y gcc g++ python3-devel curl && \
    dnf clean all && \
    rm -rf /var/cache/dnf/*

# Copy requirements and install Python dependencies
COPY requirements-simple.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-simple.txt

# Copy application code
COPY src/ src/
COPY .env.example .env
COPY data.xlsx .

# Production stage
FROM registry.access.redhat.com/ubi9/python-311:latest AS production

# Install runtime system packages
USER root
RUN dnf update -y && \
    dnf install -y curl && \
    dnf clean all && \
    rm -rf /var/cache/dnf/*

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /opt/app-root/lib/python3.11/site-packages /opt/app-root/lib/python3.11/site-packages
COPY --from=builder /opt/app-root/bin /opt/app-root/bin

# Copy application source and data
COPY --from=builder /app/src /app/src
COPY --from=builder /app/.env /app/
COPY --from=builder /app/data.xlsx /app/

# Create non-root user for security
RUN useradd -r -u 1001 -g root legaltech && \
    chown -R 1001:root /app && \
    chmod -R g=u /app

# Switch to non-root user
USER 1001

# Environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0

# Health check (simplified since we removed health endpoints)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080 || exit 1

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "src/legaltech_ai/main.py"]