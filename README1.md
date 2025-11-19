
# Genealogy Memory MCP Server

A multi-archive, structured genealogy memory service designed for AI agents.  
Implements the **Model Context Protocol (MCP)** using **Streamable HTTP** and stores structured genealogical data in **PostgreSQL**.

This server is intended to be used with:
- **OpenWebUI**
- **MetaMCP**
- Local MCP-capable agents
- Other genealogy MCP tools (e.g., mcp-openarchieven)

---

# ⭐ Key Features

- **Full genealogical data model**, including:
  - Persons  
  - Multiple life events per person  
  - Multiple addresses per person  
  - Multiple professions per person  
  - Archive/API sources  
  - Attachments (PDF, JPG, scans)  
  - Comments/notes  

- **Multi-archive ready**  
  Works with OpenArchieven, FamilySearch, Ancestry exports, scanned PDFs, etc.

- **MCP Streamable HTTP** endpoint (`/mcp`)  
  Fully compatible with OpenWebUI/MetaMCP.

- **Docker-based deployment**  
  Includes:
  - Production Dockerfile  
  - Health checks  
  - env-file driven configuration  
  - Volume persistence  

- **Automatic database initialization**  
  PostgreSQL schema is applied on first run from `db/schema.sql`.

- **Safe for long-term storage**  
  Data stored as structured rows, not free-form text.

---

# 📂 Project Structure

```
mcp-genealogy-memory/
│
├── .env
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── server/
│   └── genealogy_memory_server.py
│
└── db/
    └── schema.sql
```

---

# ⚙️ Installation

## Clone the repository

```bash
git clone https://github.com/<yourname>/mcp-genealogy-memory.git
cd mcp-genealogy-memory
```

## Start the server

```bash
docker-compose up -d --build
```

This will:

- Start PostgreSQL  
- Initialize schema from `db/schema.sql`  
- Start the MCP server on port **6555**  
- Expose `/mcp` endpoint  

---

# 🔌 MCP Endpoint

### Internal Docker network:
```
http://mcp-genealogy-memory:8020/mcp
```

### On your LAN (Unraid/NAS):
```
http://<NAS-IP>:6555/mcp
```

### Response format (standard MCP)
Every call returns:
```json
{
  "status": "ok",
  "data": { ... }
}
```
or:
```json
{
  "status": "error",
  "error": "code",
  "details": { ... }
}
```

---

# 📄 Environment Variables (.env)

```
DB_HOST=mcp-genealogy-memory-db
DB_PORT=5432
DB_NAME=genealogy
DB_USER=genealogy
DB_PASSWORD=genealogy
MEMORY_PORT=8020
```

All can be overridden at runtime.

---

# 🗄️ Database Schema (PostgreSQL)

Tables included:

- `persons`
- `events`
- `addresses`
- `professions`
- `sources`
- `attachments`
- `comments`

See `db/schema.sql` for full definitions.

The memory server handles:

- unlimited events per person  
- unlimited addresses  
- unlimited professions  
- unlimited sources  
- unlimited attachments (metadata only)  
- unlimited comments  

---

# 🧠 MCP Tools (Full Reference)

## **Person Tools**

| Tool | Description |
|------|-------------|
| `add_person` | Create a new person |
| `get_person` | Retrieve a person by ID |
| `find_persons_simple` | Search by surname / given name |

## **Source Tools**

| Tool | Description |
|------|-------------|
| `add_source` | Add metadata for an archive/API/local record |

## **Event Tools**

| Tool | Description |
|------|-------------|
| `add_event` | Add birth/marriage/death/census/residence/etc |
| `list_person_events` | Get all events for a person |

## **Profession Tools**

| Tool | Description |
|------|-------------|
| `add_profession` | Add occupation |
| `list_person_professions` | List professions |

## **Address Tools**

| Tool | Description |
|------|-------------|
| `add_address` | Add residence address |
| `list_person_addresses` | List addresses |

## **Attachment Tools**

| Tool | Description |
|------|-------------|
| `add_attachment` | Register scanned files |

## **Comment Tools**

| Tool | Description |
|------|-------------|
| `add_comment` | Add a research note |
| `list_person_comments` | Query notes |

---

# 💬 Example MCP Calls (JSON-RPC)

## List tools

```json
{
  "method": "tools.list",
  "params": {}
}
```

## Add a person

```json
{
  "method": "tools.call",
  "params": {
    "tool": "add_person",
    "arguments": {
      "given_name": "Johannes",
      "surname": "Vermeer",
      "birth_year_estimate": 1632
    }
  }
}
```

## Add an event

```json
{
  "method": "tools.call",
  "params": {
    "tool": "add_event",
    "arguments": {
      "person_id": "<UUID>",
      "event_type": "birth",
      "year": 1632,
      "place": "Delft",
      "country": "Netherlands"
    }
  }
}
```

## Search persons

```json
{
  "method": "tools.call",
  "params": {
    "tool": "find_persons_simple",
    "arguments": {
      "name_query": "vermeer"
    }
  }
}
```

---

# 🧪 Testing (Command Line)

### Test MCP connectivity

```bash
curl -X POST http://<NAS-IP>:6555/mcp \
  -H "Content-Type: application/json" \
  -d '{"method":"tools.list","params":{}}'
```

### Add a person

```bash
curl -X POST http://<NAS-IP>:6555/mcp \
  -H "Content-Type: application/json" \
  -d '{
        "method":"tools.call",
        "params":{
          "tool":"add_person",
          "arguments":{
            "given_name":"Jan",
            "surname":"Jansen"
          }
        }
      }'
```

---

# 🤖 OpenWebUI Usage Examples (Natural Language)

You can talk to your agent like this:

### Add a person

```
Add a new person named Johannes Vermeer born around 1632.
```

### Add a birth event

```
Record a birth event for Johannes Vermeer in Delft in 1632.
```

### Add a job

```
Johannes Vermeer worked as a painter in Delft around 1650.
```

### Query stored information

```
Show everything known about Johannes Vermeer in memory.
```

### Add a research note

```
Add a note that his father may have been Reynier Janszoon.
```

---

# 🧩 Agent Prompt Template (For AI Agents)

```
You have access to the "genealogy_memory" MCP server.

Use its tools to store long-term structured genealogical information:

- add_person
- add_event
- add_profession
- add_address
- add_source
- add_attachment
- add_comment

All persons may have multiple events, professions, addresses, sources, attachments, and comments.

When you retrieve data from external genealogy MCP servers (like mcp-openarchieven), store it here using structured fields.

When facts are uncertain, create a comment instead of overwriting existing data.

When answering questions, first read from genealogy_memory, then call external sources if needed.
```

---

# 🩺 Health Checks

- PostgreSQL healthcheck: `pg_isready`
- Memory MCP server healthcheck:  
  `curl -s http://localhost:${MEMORY_PORT}/mcp >/dev/null || exit 1`

Both included in `docker-compose.yml`.

---

# 🧰 Troubleshooting

### MCP server not showing tools?
- Ensure: `app = mcp.streamable_http_app()`  
- Ensure you're using **Streamable HTTP** in OpenWebUI

### Schema not created?
Delete Postgres data directory and restart:

```
rm -rf /mnt/user/appdata/network-ai/mcp-memory-genealogy/postgres-data/*
docker-compose up -d --build
```

### Connection errors?
- Wait for DB healthcheck
- Check logs:
  ```
  docker logs mcp-genealogy-memory
  ```

---

# 📜 License

MIT
