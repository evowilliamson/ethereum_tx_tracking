# QuestDB Docker Image
# Based on official QuestDB image or custom build with Java 17

FROM eclipse-temurin:17-jre-jammy

# QuestDB version
ARG QUESTDB_VERSION=9.2.3
ARG QUESTDB_ARCH=x86_64

# Install required dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/questdb

# Download and install QuestDB
# Note: QuestDB release files use -rt- and x86-64 format
RUN if [ "$QUESTDB_ARCH" = "x86_64" ]; then \
        ARCH_SUFFIX="x86-64"; \
    else \
        ARCH_SUFFIX="$QUESTDB_ARCH"; \
    fi && \
    wget -q https://github.com/questdb/questdb/releases/download/${QUESTDB_VERSION}/questdb-${QUESTDB_VERSION}-rt-linux-${ARCH_SUFFIX}.tar.gz \
    && tar -xzf questdb-${QUESTDB_VERSION}-rt-linux-${ARCH_SUFFIX}.tar.gz \
    && rm questdb-${QUESTDB_VERSION}-rt-linux-${ARCH_SUFFIX}.tar.gz \
    && mv questdb-${QUESTDB_VERSION}-rt-linux-${ARCH_SUFFIX}/* . \
    && rm -rf questdb-${QUESTDB_VERSION}-rt-linux-${ARCH_SUFFIX}

# Create symlink for questdb command
RUN ln -s /opt/questdb/bin/questdb.sh /usr/local/bin/questdb \
    && chmod +x /opt/questdb/bin/questdb.sh \
    && chmod +x /usr/local/bin/questdb

# Copy configuration file to image
COPY conf/server.conf /opt/questdb-config/server.conf

# Copy entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Create data directory (will be symlinked to volume)
RUN mkdir -p /data/questdb

# Expose ports
# 80: HTTP/Web console (Railway requirement)
# 8812: PostgreSQL wire protocol (Python app uses this)
# 9009: ILP (InfluxDB Line Protocol)
EXPOSE 80 8812 9009

# Set environment variables
ENV QUESTDB_DATA_DIR=/data/questdb
ENV JAVA_HOME=/opt/java/openjdk

# Use entrypoint script
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default: entrypoint will start QuestDB if no args provided
# Override with: docker run questdb:latest <your-command>

