#!/usr/bin/env python3
import os
import uuid
from typing import Any, Dict

import psycopg2
from psycopg2.extras import RealDictCursor

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("genealogy_memory")

DB = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

def db():
    return psycopg2.connect(**DB, cursor_factory=RealDictCursor)

def ok(data: Any) -> Dict[str, Any]:
    return {"status": "ok", "data": data}

def err(msg: str, detail: str = "") -> Dict[str, Any]:
    return {"status": "error", "error": msg, "details": detail}

# PERSON TOOLS

@mcp.tool()
def add_person(**data) -> Dict[str, Any]:
    if not data.get("given_name") and not data.get("surname"):
        return err("missing_name", "given_name or surname required")

    pid = str(uuid.uuid4())
    data.setdefault("given_name", None)
    data.setdefault("prefix", None)
    data.setdefault("surname", None)
    data.setdefault("gender", None)
    data.setdefault("birth_year_estimate", None)
    data.setdefault("death_year_estimate", None)
    data.setdefault("notes", None)
    data.setdefault("full_name_normalized", None)
    data.setdefault("confidence_score", 1.0)
    data["person_id"] = pid

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO persons (
                person_id, given_name, prefix, surname, gender,
                birth_year_estimate, death_year_estimate,
                notes, full_name_normalized, confidence_score
            ) VALUES (
                %(person_id)s, %(given_name)s, %(prefix)s, %(surname)s, %(gender)s,
                %(birth_year_estimate)s, %(death_year_estimate)s,
                %(notes)s, %(full_name_normalized)s, %(confidence_score)s
            )""",
            data,
        )
    return ok({"person_id": pid})

@mcp.tool()
def get_person(person_id: str) -> Dict[str, Any]:
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM persons WHERE person_id=%s", (person_id,))
        row = cur.fetchone()
        if not row:
            return err("not_found", f"person_id={person_id}")
    return ok(row)

@mcp.tool()
def find_persons_simple(name_query: str, limit: int = 10) -> Dict[str, Any]:
    if not name_query.strip():
        return err("missing_query", "name_query is required")
    limit = max(1, min(limit, 100))
    like = f"%{name_query}%"
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT *
               FROM persons
               WHERE given_name ILIKE %s OR surname ILIKE %s OR full_name_normalized ILIKE %s
               ORDER BY surname NULLS LAST, given_name NULLS LAST
               LIMIT %s""",
            (like, like, like, limit),
        )
        rows = cur.fetchall()
    return ok({"count": len(rows), "persons": rows})

# SOURCE TOOLS

@mcp.tool()
def add_source(**data) -> Dict[str, Any]:
    sid = str(uuid.uuid4())
    data.setdefault("source_type", None)
    data.setdefault("archive_code", None)
    data.setdefault("archive_name", None)
    data.setdefault("identifier", None)
    data.setdefault("url", None)
    data.setdefault("collection", None)
    data.setdefault("document_number", None)
    data.setdefault("registry_number", None)
    data.setdefault("institution_name", None)
    data.setdefault("raw_json", None)
    data.setdefault("notes", None)
    data["source_id"] = sid

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO sources (
                source_id, source_type, archive_code, archive_name,
                identifier, url, collection, document_number,
                registry_number, institution_name, raw_json, notes
            ) VALUES (
                %(source_id)s, %(source_type)s, %(archive_code)s, %(archive_name)s,
                %(identifier)s, %(url)s, %(collection)s, %(document_number)s,
                %(registry_number)s, %(institution_name)s, %(raw_json)s, %(notes)s
            )""",
            data,
        )
    return ok({"source_id": sid})

# EVENT TOOLS

@mcp.tool()
def add_event(**data) -> Dict[str, Any]:
    if not data.get("person_id"):
        return err("missing_person_id")
    if not data.get("event_type"):
        return err("missing_event_type")

    eid = str(uuid.uuid4())
    data.setdefault("date_literal", None)
    data.setdefault("year", None)
    data.setdefault("month", None)
    data.setdefault("day", None)
    data.setdefault("place", None)
    data.setdefault("country", None)
    data.setdefault("source_id", None)
    data.setdefault("notes", None)
    data["event_id"] = eid

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO events (
                event_id, person_id, event_type, date_literal,
                year, month, day, place, country, source_id, notes
            ) VALUES (
                %(event_id)s, %(person_id)s, %(event_type)s, %(date_literal)s,
                %(year)s, %(month)s, %(day)s, %(place)s, %(country)s,
                %(source_id)s, %(notes)s
            )""",
            data,
        )
    return ok({"event_id": eid})

@mcp.tool()
def list_person_events(person_id: str) -> Dict[str, Any]:
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT *
               FROM events
               WHERE person_id=%s
               ORDER BY year NULLS LAST, month NULLS LAST, day NULLS LAST""",
            (person_id,),
        )
        rows = cur.fetchall()
    return ok({"count": len(rows), "events": rows})

# PROFESSION TOOLS

@mcp.tool()
def add_profession(**data) -> Dict[str, Any]:
    if not data.get("person_id"):
        return err("missing_person_id")
    if not data.get("title"):
        return err("missing_title")

    prof_id = str(uuid.uuid4())
    data.setdefault("start_year", None)
    data.setdefault("end_year", None)
    data.setdefault("location", None)
    data.setdefault("source_id", None)
    data.setdefault("notes", None)
    data["profession_id"] = prof_id

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO professions (
                profession_id, person_id, title, start_year,
                end_year, location, source_id, notes
            ) VALUES (
                %(profession_id)s, %(person_id)s, %(title)s,
                %(start_year)s, %(end_year)s, %(location)s,
                %(source_id)s, %(notes)s
            )""",
            data,
        )
    return ok({"profession_id": prof_id})

# ADDRESS TOOLS

@mcp.tool()
def add_address(**data) -> Dict[str, Any]:
    if not data.get("person_id"):
        return err("missing_person_id")

    aid = str(uuid.uuid4())
    data.setdefault("street", None)
    data.setdefault("house_number", None)
    data.setdefault("city", None)
    data.setdefault("province", None)
    data.setdefault("country", None)
    data.setdefault("start_year", None)
    data.setdefault("end_year", None)
    data.setdefault("source_id", None)
    data.setdefault("notes", None)
    data["address_id"] = aid

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO addresses (
                address_id, person_id, street, house_number,
                city, province, country, start_year, end_year,
                source_id, notes
            ) VALUES (
                %(address_id)s, %(person_id)s, %(street)s, %(house_number)s,
                %(city)s, %(province)s, %(country)s, %(start_year)s,
                %(end_year)s, %(source_id)s, %(notes)s
            )""",
            data,
        )
    return ok({"address_id": aid})

# ATTACHMENT TOOLS

@mcp.tool()
def add_attachment(**data) -> Dict[str, Any]:
    att_id = str(uuid.uuid4())
    data.setdefault("source_id", None)
    data.setdefault("person_id", None)
    data.setdefault("file_name", None)
    data.setdefault("file_type", None)
    data.setdefault("file_path", None)
    data.setdefault("description", None)
    data["attachment_id"] = att_id

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO attachments (
                attachment_id, source_id, person_id,
                file_name, file_type, file_path, description
            ) VALUES (
                %(attachment_id)s, %(source_id)s, %(person_id)s,
                %(file_name)s, %(file_type)s, %(file_path)s, %(description)s
            )""",
            data,
        )
    return ok({"attachment_id": att_id})

# COMMENT TOOLS

@mcp.tool()
def add_comment(**data) -> Dict[str, Any]:
    if not data.get("text"):
        return err("missing_text")

    cid = str(uuid.uuid4())
    data.setdefault("person_id", None)
    data.setdefault("source_id", None)
    data.setdefault("author", None)
    data["comment_id"] = cid

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO comments (
                comment_id, person_id, source_id, author, text
            ) VALUES (
                %(comment_id)s, %(person_id)s, %(source_id)s,
                %(author)s, %(text)s
            )""",
            data,
        )
    return ok({"comment_id": cid})

app = mcp.streamable_http_app()
