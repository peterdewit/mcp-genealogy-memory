# Genealogy Memory MCP Server

A production-ready, self-contained genealogy research memory server designed to operate as an MCP tool for LLM agents. This service stores structured genealogical data such as persons, events, addresses, relationships, sources, and attachments, while providing a clean tool API for automated research agents.

This README covers:

* Overview
* Features
* Requirements
* Directory structure
* Installation
* Development usage
* Production deployment
* Resetting the database
* Backup and restore
* Tools reference (summary)
* Let's Encrypt TLS (Traefik)
* Troubleshooting
* License

---

# Overview

The Genealogy Memory MCP Server exposes tool endpoints an AI agent can call to:

* Add and search persons
* Record events, addresses, professions, relationships
* Store metadata on archival sources
* Log web crawls
* Save attachments
* Track duplicates and verification status

Backend: **PostgreSQL 16**
Server: **Python FastAPI + MCP**

---

# Features

* Full genealogy data model
* Modular MCP tool definitions
* Safe UUID-based primary keys
* Crawl log for avoiding repeated scraping
* Attachments metadata + optional downloader
* Relationship mapping and duplicate marking
* Ready for containerized deployment

---

# Requirements

* Docker
* Docker Compose (v2 recommended)
* Python 3.11+ if running outside containers

Optional production components:

* Traefik (reverse proxy)
* Let's Encrypt TLS
* Offsite backups

---

# Directory Structure

```text
genealogy-memory-mcp/
├── Dockerfile
├── server.py
├── schema.sql
├── requirements.txt
├── reset_genealogy_memory.sh
├── docker-compose.production.yml
├── docker-compose.override.yml
└── .env.example
```

---

# Installation

## 1. Clone repository

```bash
git clone https://github.com/yourname/genealogy-memory-mcp.git
cd genealogy-memory-mcp
```

## 2. Copy environment file

```bash
cp .env.example .env
```

Adjust credentials if needed.

## 3. Build the container

```bash
docker build -t genealogy-memory-mcp .
```

---

# Development Usage

Start the stack:

```bash
docker compose up -d
```

This uses:

* `docker-compose.yml` (development)
* `docker-compose.override.yml` (hot-reload + debug, if present)

The MCP server will be available at:

```text
http://localhost:6555/mcp
```

---

# Production Deployment

Use:

```bash
docker compose -f docker-compose.production.yml --env-file .env up -d
```

Production includes:

* Restart policies (`restart: always`)
* Healthchecks for both services
* Named volume for stable database storage
* No development mounts

## Environment Variables

Set these in `.env`:

```env
DB_HOST=genealogy-memory-db
DB_PORT=5432
DB_NAME=genealogy
DB_USER=genealogy
DB_PASSWORD=your_secure_password
```

---

# Resetting the Database

Use the universal reset tool:

```bash
./reset_genealogy_memory.sh
```

This will:

* Stop containers
* Remove containers
* Destroy `db-data` directory (or `DATA_DIR` override)
* Recreate PostgreSQL
* Apply `schema.sql`

Override paths:

```bash
DATA_DIR=/custom/dir SCHEMA_FILE=./schema.sql ./reset_genealogy_memory.sh
```

This **erases all genealogy data**.

---

# Backup & Restore

## Backup PostgreSQL

```bash
docker exec genealogy-memory-db pg_dump -U genealogy genealogy > backup.sql
```

## Restore

```bash
cat backup.sql | docker exec -i genealogy-memory-db psql -U genealogy -d genealogy
```

---

## Tools Reference (Summary)

Below is a concise summary of the MCP tools exposed by this server. Each tool is available to any MCP-compatible client or agent.

### Person Tools

* **add_person** – Create a new person record.
* **get_person** – Retrieve a person by UUID.
* **find_persons_simple** – Search by partial name.
* **set_person_verified** – Mark a person as verified/unverified.
* **set_person_status** – Update research status and notes.

### Source Tools

* **add_source** – Add metadata for archival or external records.

### Event Tools

* **add_event** – Add life events (birth, marriage, death, etc.).
* **list_person_events** – List events for a person.

### Profession Tools

* **add_profession** – Add a job or occupation.
* **list_person_professions** – List all jobs for a person.

### Address Tools

* **add_address** – Add address or residence information.
* **list_person_addresses** – List addresses for a person.

### Attachment Tools

* **add_attachment** – Add metadata for attached files.
* **add_attachment_metadata** – Register downloadable attachments.
* **fetch_attachments_for_person** – Download attachments flagged for fetching.

### Comment Tools

* **add_comment** – Add a free-text comment.
* **list_person_comments** – List comments for a person.

### Relationship Tools

* **add_relationship** – Create relationships (parent, spouse, sibling, etc.).
* **get_person_relationships** – Get relationships for a person.
* **set_possible_duplicate_of** – Mark a record as a possible duplicate.

### Crawl Tools

* **log_crawl** – Log crawled URL metadata.
* **get_unprocessed_crawls** – List crawl entries needing processing.
* **mark_crawl_processed** – Mark a crawl record as processed.

---

# Let's Encrypt TLS (Traefik)

To run the MCP server behind HTTPS using Traefik/Let's Encrypt:

## Requirements

* A domain name (example: `genealogy.yourdomain.com`)
* DNS pointing to your server's public IP
* Traefik running as reverse proxy
* Ports 80 and 443 open

## Example Traefik labels

Add to the MCP service in production compose:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.genealogy.rule=Host(`genealogy.yourdomain.com`)"
  - "traefik.http.routers.genealogy.entrypoints=websecure"
  - "traefik.http.routers.genealogy.tls.certresolver=letsencrypt"
  - "traefik.http.services.genealogy.loadbalancer.server.port=8020"
```

This exposes:

```text
https://genealogy.yourdomain.com
```

with automatic TLS from Let's Encrypt.

Traefik must be set up separately with:

* ACME storage (`acme.json`)
* Let's Encrypt resolver
* Web & websecure entrypoints

---

# Troubleshooting

## Postgres not ready

If API shows connection failures, ensure:

```bash
docker exec genealogy-memory-db pg_isready -U genealogy -d genealogy
```

## MCP not reachable

Check logs:

```bash
docker logs genealogy-memory
```

## Container crashes on start

Likely a schema mismatch:

```bash
docker exec -it genealogy-memory-db psql -U genealogy -d genealogy -c "\dt"
```

Confirm tables exist.

---

# License

MIT

---


