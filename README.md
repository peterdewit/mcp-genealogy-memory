# Genealogy Memory MCP Server

Structured genealogy memory service using PostgreSQL and Model Context Protocol (MCP).

- Stores persons, life events, professions, addresses, sources, attachments, and comments.
- Supports multiple archives and multiple events/addresses/jobs per person.
- Exposes a Streamable HTTP MCP endpoint at `/mcp`.

## Endpoint

Inside Docker network:

- `http://mcp-genealogy-memory:${MEMORY_PORT}/mcp`

From LAN:

- `http://<NAS-IP>:6555/mcp`

## Running

```bash
docker-compose up -d --build
```

PostgreSQL schema is applied from `db/schema.sql` on first start.

Persistent data is stored in:

- `/mnt/user/appdata/network-ai/mcp-memory-genealogy/postgres-data` (host)

## MCP Call Examples

### List tools

```json
{
  "method": "tools.list",
  "params": {}
}
```

### Add person

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

### Add event

```json
{
  "method": "tools.call",
  "params": {
    "tool": "add_event",
    "arguments": {
      "person_id": "UUID_FROM_add_person",
      "event_type": "birth",
      "year": 1632,
      "place": "Delft",
      "country": "Netherlands"
    }
  }
}
```

### Search persons

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

## Agent Prompt Template

Use this as a system/tool prompt for an agent that talks to this server:

```text
You have access to the "genealogy_memory" MCP server.

Use it to store long-term structured genealogical information:

- add_person: create new people
- add_event: record life events (birth, baptism, marriage, death, residence, census, etc.)
- add_profession: store occupations across time
- add_address: store residential addresses
- add_source: store archive/API source metadata
- add_attachment: link file paths for scans/pdfs/images
- add_comment: store free-text research notes

A single person may have multiple events, addresses, professions, sources, attachments, and comments.

When you learn a new genealogical fact:
- store it as a structured event/address/profession with a link to a source when possible
- if uncertain, add a comment explaining the hypothesis instead of overwriting or merging people

When answering questions:
- read from genealogy_memory first
- then optionally call external archive MCP servers if available
- write new findings back into genealogy_memory
```

## Testing

### Command line (curl)

Test tools list:

```bash
curl -X POST http://<NAS-IP>:6555/mcp \
  -H "Content-Type: application/json" \
  -d '{"method":"tools.list","params":{}}'
```

Add a person:

```bash
curl -X POST http://<NAS-IP>:6555/mcp \
  -H "Content-Type: application/json" \
  -d '{
        "method":"tools.call",
        "params":{
          "tool":"add_person",
          "arguments":{
            "given_name":"Johannes",
            "surname":"Vermeer",
            "birth_year_estimate":1632
          }
        }
      }'
```

### OpenWebUI chat examples

Example user prompts once the MCP tool is connected:

- "Add a new person named Johannes Vermeer born around 1632."
- "Record a birth event for Johannes Vermeer in 1632 in Delft, Netherlands."
- "What events are recorded for Johannes Vermeer in memory?"
- "Add a note that his father may be Reynier Janszoon and verify later."

The agent should translate these into appropriate MCP tool calls.

## License

MIT
