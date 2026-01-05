# Docker Setup Explanation

This document explains how Docker works and what each file does in our QuestDB setup.

## What is Docker?

Docker is a containerization platform that packages an application and its dependencies into a "container" - a lightweight, portable unit that runs the same way everywhere.

**Key Concepts:**
- **Image**: A read-only template/blueprint (like a recipe)
- **Container**: A running instance of an image (like a running application)
- **Volume**: Persistent storage that survives container restarts
- **Port Mapping**: Connecting container ports to host ports

**Analogy:**
- **Image** = A recipe (Dockerfile)
- **Container** = A cake made from the recipe (running application)
- **Volume** = A storage box that persists even if you throw away the cake

---

## Our QuestDB Docker Setup - File by File

### 1. `Dockerfile` - The Blueprint

**What it does:** Defines how to build the QuestDB Docker image.

**Step-by-step explanation:**

```dockerfile
FROM eclipse-temurin:17-jre-jammy
```
- **Starts with a base image** containing Java 17 runtime
- Like starting with a pre-made cake base

```dockerfile
RUN apt-get update && apt-get install -y wget curl
```
- **Installs tools** needed to download QuestDB
- Like getting mixing bowls and spoons

```dockerfile
RUN wget -q https://github.com/questdb/questdb/releases/download/...
```
- **Downloads and installs QuestDB** binary
- Like adding the main ingredient to the cake

```dockerfile
COPY conf/server.conf /opt/questdb-config/server.conf
```
- **Copies your config file** from your project into the image
- Like adding a custom decoration that's part of the recipe

```dockerfile
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
```
- **Copies the startup script** into the image
- Like adding instructions on how to serve the cake

```dockerfile
EXPOSE 80 8812 9009
```
- **Documents which ports** the container will use
- Like labeling which doors the cake will be served through

```dockerfile
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```
- **Sets the entrypoint script** to run when container starts
- Like saying "always follow these instructions when serving"

**When it runs:** Only when you build the image (`docker build`)

---

### 2. `entrypoint.sh` - The Startup Script

**What it does:** Runs every time the container starts. Sets up the environment and starts QuestDB.

**Why we need it:**
- Docker containers are "stateless" - they start fresh each time
- We need to set up symlinks and copy config files at startup
- This script does that setup automatically

**Step-by-step explanation:**

```bash
mkdir -p "${QUESTDB_DATA_DIR:-/data/questdb}"
```
- **Creates the data directory** (or uses mounted volume)
- Like preparing a storage box for the cake

```bash
ln -sf "${QUESTDB_DATA_DIR:-/data/questdb}" ~/.questdb
```
- **Creates a symlink** from `~/.questdb` to `/data/questdb`
- Like creating a shortcut so QuestDB can find its data using its default path

```bash
cp /opt/questdb-config/server.conf "${QUESTDB_DATA_DIR:-/data/questdb}/conf/server.conf"
```
- **Copies config file** from image to the volume location
- Like copying the recipe card to the storage box so it's always available

```bash
exec questdb start -d ~/.questdb
```
- **Starts QuestDB** using the symlinked path
- Like actually serving the cake

**When it runs:** Every time the container starts (`docker run` or `docker start`)

---

### 3. `conf/server.conf` - The Configuration File

**What it does:** Contains QuestDB settings (ports, bindings, etc.)

**Key setting:**
```
http.bind.to=0.0.0.0:80
```
- **Tells QuestDB to listen on port 80** (Railway requirement)
- Like telling the cake to be served at a specific door

**Why it's in the project:**
- Version controlled (you can track changes)
- Part of the Docker image (baked in during build)
- Copied to volume at startup (so it persists)

**When it's used:** QuestDB reads this file when it starts

---

### 4. `docker-compose.yml` - The Orchestration File

**What it does:** Defines how to run the container (ports, volumes, environment variables)

**Step-by-step explanation:**

```yaml
build:
  context: .
  dockerfile: Dockerfile
```
- **Tells Docker Compose** to build the image using our Dockerfile
- Like saying "use this recipe"

```yaml
ports:
  - "80:80"
  - "8812:8812"
  - "9009:9009"
```
- **Maps container ports to host ports**
- Format: `host:container`
- Like connecting doors: host port 80 → container port 80

```yaml
volumes:
  - questdb_data:/data/questdb
```
- **Mounts a persistent volume** at `/data/questdb`
- Like attaching a storage box that survives container restarts

```yaml
environment:
  - QUESTDB_DATA_DIR=/data/questdb
```
- **Sets environment variables** inside the container
- Like setting labels on the storage box

**When it runs:** When you run `docker-compose up`

---

## How It All Works Together

### Build Time (Creating the Image)

```
1. You run: docker build -t questdb:latest .
2. Docker reads Dockerfile
3. Docker:
   - Starts with Java 17 base image
   - Installs wget/curl
   - Downloads QuestDB
   - Copies server.conf into image
   - Copies entrypoint.sh into image
   - Sets entrypoint
4. Result: A Docker image (like a packaged application)
```

### Runtime (Starting the Container)

```
1. You run: docker-compose up (or docker run)
2. Docker creates a container from the image
3. Docker mounts the volume at /data/questdb
4. Docker runs entrypoint.sh:
   - Creates /data/questdb directory
   - Creates symlink ~/.questdb → /data/questdb
   - Copies server.conf to /data/questdb/conf/
   - Starts QuestDB
5. QuestDB reads server.conf and starts on port 80
6. Result: QuestDB running and accessible
```

### Data Flow

```
Your Project:
  questdb/conf/server.conf
       ↓ (COPY in Dockerfile)
Docker Image:
  /opt/questdb-config/server.conf
       ↓ (cp in entrypoint.sh)
Container Volume:
  /data/questdb/conf/server.conf
       ↓ (via symlink)
QuestDB sees:
  ~/.questdb/conf/server.conf
```

---

## Key Docker Concepts in Our Setup

### 1. **Image vs Container**
- **Image**: The blueprint (built from Dockerfile)
- **Container**: Running instance (created from image)

### 2. **Volume Mounting**
- `/data/questdb` is a volume mount
- Data persists even if container is deleted
- Like external storage that survives container restarts

### 3. **Port Mapping**
- `"80:80"` means: host port 80 → container port 80
- Allows you to access QuestDB from your host machine

### 4. **Entrypoint vs CMD**
- **ENTRYPOINT**: Always runs (our setup script)
- **CMD**: Default command (can be overridden)
- In our case: entrypoint sets up, then starts QuestDB

### 5. **Symlink Strategy**
- QuestDB expects data at `~/.questdb`
- We store data in `/data/questdb` (volume)
- Symlink connects them: `~/.questdb` → `/data/questdb`
- QuestDB uses default path, but data persists in volume

---

## Common Commands

```bash
# Build the image
docker build -t questdb:latest questdb/

# Run with docker-compose (easiest)
cd questdb
docker-compose up -d

# Run manually
docker run -d \
  -p 80:80 -p 8812:8812 -p 9009:9009 \
  -v questdb_data:/data/questdb \
  questdb:latest

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Access container shell
docker exec -it questdb bash
```

---

## Why This Setup?

1. **Port 80 in config**: Railway requires port 80, not 9000
2. **Config in project**: Version controlled, easy to modify
3. **Config copied at startup**: Ensures it's always in the right place
4. **Symlink strategy**: QuestDB uses default path, but data persists
5. **Volume mounting**: Data survives container restarts/deletions

---

## Summary

- **Dockerfile**: Recipe for building the image (runs once during build)
- **entrypoint.sh**: Startup script (runs every time container starts)
- **server.conf**: Configuration file (read by QuestDB)
- **docker-compose.yml**: Orchestration file (defines how to run)

The flow: Build image → Start container → Entrypoint runs → QuestDB starts → Ready!

