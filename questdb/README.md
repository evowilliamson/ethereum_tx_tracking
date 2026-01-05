# QuestDB Docker Setup

This directory contains the Docker configuration for QuestDB with Railway-compatible settings.

## Structure

```
questdb/
├── conf/
│   └── server.conf          # QuestDB configuration (port 80 for Railway)
├── Dockerfile               # QuestDB Docker image definition
├── entrypoint.sh            # Container startup script
├── docker-compose.yml       # Docker Compose configuration (for local dev)
└── README.md               # This file
```

## Configuration

The `server.conf` file configures QuestDB to:
- Listen on port 80 for HTTP/Web console (Railway requirement)
- Use default ports for PostgreSQL (8812) and ILP (9009)

## Building the Image

```bash
cd questdb
docker build -t questdb:latest .
```

## Running Locally

### Using Docker Compose (Recommended)

```bash
cd questdb
docker-compose up -d
```

### Using Docker Run

```bash
docker run -d \
  --name questdb \
  -p 80:80 \
  -p 8812:8812 \
  -p 9009:9009 \
  -v questdb_data:/data/questdb \
  questdb:latest
```

## Access

- **Web Console**: http://localhost:80
- **PostgreSQL Wire Protocol**: localhost:8812 (used by Python app)
- **ILP**: localhost:9009

## Data Persistence

Data is stored in the Docker volume `/data/questdb`. The container creates a symlink `~/.questdb` → `/data/questdb` so QuestDB uses its default path while data persists in the volume.

## Configuration File

The `server.conf` file is:
1. Copied into the Docker image during build
2. Copied to the volume location at container startup
3. Available at `~/.questdb/conf/server.conf` (via symlink)

To modify the configuration:
1. Edit `conf/server.conf` in this directory
2. Rebuild the Docker image
3. Restart the container

## Railway Deployment

For Railway deployment:
1. Build the image (Railway will do this automatically if you push the code)
2. Ensure port 80 is exposed (configured in `server.conf`)
3. Mount a persistent volume at `/data/questdb`

## Environment Variables

- `QUESTDB_DATA_DIR`: Data directory path (default: `/data/questdb`)

