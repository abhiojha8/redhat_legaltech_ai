# -------- Stage 1: Builder --------
FROM registry.access.redhat.com/ubi9/python-311:latest AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for ChromaDB and ML libraries
USER root
RUN dnf update -y && \
    dnf remove -y curl-minimal || true && \
    dnf install -y gcc g++ python3-devel curl --allowerasing && \
    dnf clean all && \
    rm -rf /var/cache/dnf/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and example env/data
COPY src/ src/
COPY .env.example .env
COPY data/ data/

# -------- Stage 2: Production --------
FROM registry.access.redhat.com/ubi9/python-311:latest AS production

USER root
# Install only runtime system packages
RUN dnf update -y && \
    dnf remove -y curl-minimal || true && \
    dnf install -y curl --allowerasing && \
    dnf clean all && \
    rm -rf /var/cache/dnf/*

WORKDIR /app

# Copy installed packages and app code from builder
COPY --from=builder /opt/app-root/lib/python3.11/site-packages /opt/app-root/lib/python3.11/site-packages
COPY --from=builder /opt/app-root/bin /opt/app-root/bin
COPY --from=builder /app/src /app/src
COPY --from=builder /app/.env /app/
COPY --from=builder /app/data /app/data

# Fix permissions for non-root execution
RUN chown -R 1001:root /app && chmod -R g=u /app

# Switch to OpenShift-compatible non-root user (already present in UBI image)
USER 1001

# Environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0

# Health check (can be modified for your real endpoints)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080 || exit 1

EXPOSE 8080

# Run the application
CMD ["python", "src/legaltech_ai/main.py"]
