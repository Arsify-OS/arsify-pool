# Generic Custom Dockerfile for VPSO Agents (Hermes-Agent Base)
# Adapted from NanoClaw-v2 container patterns
FROM nousresearch/hermes-agent:latest

# Bootstrap pip in the Hermes venv (if not present)
RUN curl -fsSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py && \
    /opt/hermes/.venv/bin/python3 /tmp/get-pip.py && \
    rm /tmp/get-pip.py

# Install required Python dependencies (add/remove as needed for your agent)
RUN /opt/hermes/.venv/bin/pip install --no-cache-dir requests beautifulsoup4 lxml

# Copy agent scripts to container
COPY scripts/ /app/scripts/

# Make scripts executable
RUN chmod +x /app/scripts/*.py

WORKDIR /app

# Set entrypoint to your agent script (adjust path as needed)
ENTRYPOINT ["/opt/hermes/.venv/bin/python3", "/app/scripts/your_agent_script.py"]