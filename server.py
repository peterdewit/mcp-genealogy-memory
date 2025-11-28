#!/usr/bin/env python3
import os
import uuid
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from mcp.server.fastmcp import FastMCP

import requests
from pathlib import Path

# ----------------------------------------------------------
# MCP INIT
# ----------------------------------------------------------

mcp = FastMCP("genealogy_memory")

# DB configuration via environment, with sensible defaults
DB = {
    "host": os.getenv("DB_HOST", "db"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "genealogy"),
    "user": os.getenv("DB_USER", "genealogy"),
    "password": os.getenv("DB_PASSWORD", "genealogy"),
}


def db_conn():
    return psycopg2.connect(**DB, cursor_factory=RealDictCursor)


def ok(data: Any) -> Dict[str, Any]:
    return {"status": "ok", "data": data}


def err(code: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {"status": "error", "error": code, "details": details or {}}


# ----------------------------------------------------------
# PERSON TOOLS
# ----------------------------------------------------------

@mcp.tool()
def add_person(
    given_name: str = "",
    prefix: str = "",
    surname: str = "",
    gender: str = "",
    birth_year_estimate: int = 0,
    death_year_estimate: int = 0,
    notes: str = "",
    full_name_normalized: str = "",
    confidence_score: float = 1.0,
) -> Dict[str, Any]:
    """
    Create a new person. All fields optional except surname OR given_name.
    """
    if not given_name and not surname:
        return err("missing_name", {"message": "At least given_name or surname is required"})

    pid = str(uuid.uuid4())
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO persons (
                person_id, given_name, prefix, surname, gender,
                birth_year_estimate, death_year_estimate, notes,
                full_name_normalized, confidence_score
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                pid,
                given_name or None,
                prefix or None,
                surname or None,
                gender or None,
                birth_year_estimate or None,
                death_year_estimate or None,
                notes or None,
                full_name_normalized or None,
                confidence_score,
            ),
        )
    return ok({"person_id": pid})


@mcp.tool()
def get_person(person_id: str) -> Dict[str, Any]:
    """
    Retrieve a person by ID, including basic details only.
    """
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM persons WHERE person_id = %s", (person_id,))
        row = cur.fetchone()
        if not row:
            return err("not_found", {"person_id": person_id})
        return ok(row)


@mcp.tool()
def find_persons_simple(
    name_query: str,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Simple search on surname and given_name using ILIKE.
    Agents should pass partial or full name.
    """
    if not name_query.strip():
        return err("missing_query", {"message": "name_query is required"})
    limit = max(1, min(limit, 100))

    like = f"%{name_query}%"
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM persons
            WHERE (surname ILIKE %s OR given_name ILIKE %s OR full_name_normalized ILIKE %s)
            ORDER BY surname NULLS LAST, given_name NULLS LAST
            LIMIT %s
            """,
            (like, like, like, limit),
        )
        rows = cur.fetchall()
    return ok({"count": len(rows), "persons": rows})


# ----------------------------------------------------------
# SOURCE TOOLS
# ----------------------------------------------------------

@mcp.tool()
def add_source(
    source_type: str = "",
    archive_code: str = "",
    archive_name: str = "",
    identifier: str = "",
    url: str = "",
    collection: str = "",
    document_number: str = "",
    registry_number: str = "",
    institution_name: str = "",
    raw_json: str = "",
    notes: str = "",
    image_url: str = "",
    crawl_url: str = "",
) -> Dict[str, Any]:
    """
    Add a source definition (archive/API/local document).
    raw_json should be a JSON string if provided.
    Optionally link to crawl_log via crawl_url (if exists).
    """
    sid = str(uuid.uuid4())
    raw_json_text = raw_json or None

    with db_conn() as conn, conn.cursor() as cur:
        crawl_id = None
        if crawl_url:
            cur.execute(
                "SELECT crawl_id FROM crawl_log WHERE url = %s",
                (crawl_url,),
            )
            row = cur.fetchone()
            if row:
                crawl_id = row["crawl_id"]

        cur.execute(
            """
            INSERT INTO sources (
                source_id, source_type, archive_code, archive_name,
                identifier, url, collection, document_number,
                registry_number, institution_name, raw_json, notes,
                image_url, crawl_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                sid,
                source_type or None,
                archive_code or None,
                archive_name or None,
                identifier or None,
                url or None,
                collection or None,
                document_number or None,
                registry_number or None,
                institution_name or None,
                raw_json_text,
                notes or None,
                image_url or None,
                crawl_id,
            ),
        )
    return ok({"source_id": sid})


# ----------------------------------------------------------
# EVENT TOOLS
# ----------------------------------------------------------

@mcp.tool()
def add_event(
    person_id: str,
    event_type: str,
    date_literal: str = "",
    year: int = 0,
    month: int = 0,
    day: int = 0,
    place: str = "",
    country: str = "",
    source_id: str = "",
    notes: str = "",
) -> Dict[str, Any]:
    """
    Add a life event for a person (birth, marriage, death, census, residence, etc.).
    """
    if not person_id:
        return err("missing_person_id")
    if not event_type:
        return err("missing_event_type")

    eid = str(uuid.uuid4())
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO events (
                event_id, person_id, event_type, date_literal,
                year, month, day, place, country, source_id, notes
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                eid,
                person_id,
                event_type,
                date_literal or None,
                year or None,
                month or None,
                day or None,
                place or None,
                country or None,
                source_id or None,
                notes or None,
            ),
        )
    return ok({"event_id": eid})


@mcp.tool()
def list_person_events(person_id: str) -> Dict[str, Any]:
    """
    List all events for a person.
    """
    if not person_id:
        return err("missing_person_id")
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM events
            WHERE person_id = %s
            ORDER BY year NULLS LAST, month NULLS LAST, day NULLS LAST
            """,
            (person_id,),
        )
        rows = cur.fetchall()
    return ok({"count": len(rows), "events": rows})


# ----------------------------------------------------------
# PROFESSION TOOLS
# ----------------------------------------------------------

@mcp.tool()
def add_profession(
    person_id: str,
    title: str,
    start_year: int = 0,
    end_year: int = 0,
    location: str = "",
    source_id: str = "",
    notes: str = "",
) -> Dict[str, Any]:
    """
    Add a profession/job for a person.
    """
    if not person_id:
        return err("missing_person_id")
    if not title:
        return err("missing_title")

    prof_id = str(uuid.uuid4())
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO professions (
                profession_id, person_id, title, start_year,
                end_year, location, source_id, notes
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                prof_id,
                person_id,
                title,
                start_year or None,
                end_year or None,
                location or None,
                source_id or None,
                notes or None,
            ),
        )
    return ok({"profession_id": prof_id})


@mcp.tool()
def list_person_professions(person_id: str) -> Dict[str, Any]:
    """
    List all professions/jobs for a person.
    """
    if not person_id:
        return err("missing_person_id")
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM professions
            WHERE person_id = %s
            ORDER BY start_year NULLS LAST
            """,
            (person_id,),
        )
        rows = cur.fetchall()
    return ok({"count": len(rows), "professions": rows})


# ----------------------------------------------------------
# ADDRESS TOOLS
# ----------------------------------------------------------

@mcp.tool()
def add_address(
    person_id: str,
    street: str = "",
    house_number: str = "",
    city: str = "",
    province: str = "",
    country: str = "",
    start_year: int = 0,
    end_year: int = 0,
    source_id: str = "",
    notes: str = "",
) -> Dict[str, Any]:
    """
    Add a residential address for a person (can be multiple over time).
    """
    if not person_id:
        return err("missing_person_id")

    addr_id = str(uuid.uuid4())
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO addresses (
                address_id, person_id, street, house_number,
                city, province, country, start_year, end_year,
                source_id, notes
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                addr_id,
                person_id,
                street or None,
                house_number or None,
                city or None,
                province or None,
                country or None,
                start_year or None,
                end_year or None,
                source_id or None,
                notes or None,
            ),
        )
    return ok({"address_id": addr_id})


@mcp.tool()
def list_person_addresses(person_id: str) -> Dict[str, Any]:
    """
    List all addresses/residences for a person.
    """
    if not person_id:
        return err("missing_person_id")
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM addresses
            WHERE person_id = %s
            ORDER BY start_year NULLS LAST
            """,
            (person_id,),
        )
        rows = cur.fetchall()
    return ok({"count": len(rows), "addresses": rows})


# ----------------------------------------------------------
# ATTACHMENTS TOOLS
# ----------------------------------------------------------

@mcp.tool()
def add_attachment(
    source_id: str = "",
    person_id: str = "",
    file_name: str = "",
    file_type: str = "",
    file_path: str = "",
    description: str = "",
) -> Dict[str, Any]:
    """
    Register an attachment (image/PDF/etc) by path.
    The file is managed externally; this record is metadata only.
    """
    if not file_name and not file_path:
        return err("missing_file_info")

    att_id = str(uuid.uuid4())
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO attachments (
                attachment_id, source_id, person_id,
                file_name, file_type, file_path, description
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                att_id,
                source_id or None,
                person_id or None,
                file_name or None,
                file_type or None,
                file_path or None,
                description or None,
            ),
        )
    return ok({"attachment_id": att_id})


# ----------------------------------------------------------
# COMMENTS TOOLS
# ----------------------------------------------------------

@mcp.tool()
def add_comment(
    person_id: str = "",
    source_id: str = "",
    author: str = "",
    text: str = "",
) -> Dict[str, Any]:
    """
    Add a free-text comment or note.
    """
    if not text:
        return err("missing_text")

    cid = str(uuid.uuid4())
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO comments (
                comment_id, person_id, source_id, author, text
            ) VALUES (%s,%s,%s,%s,%s)
            """,
            (
                cid,
                person_id or None,
                source_id or None,
                author or None,
                text,
            ),
        )
    return ok({"comment_id": cid})


@mcp.tool()
def list_person_comments(person_id: str) -> Dict[str, Any]:
    """
    List all comments for a person.
    """
    if not person_id:
        return err("missing_person_id")

    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM comments
            WHERE person_id = %s
            ORDER BY created_at
            """,
            (person_id,),
        )
        rows = cur.fetchall()
    return ok({"count": len(rows), "comments": rows})


# ----------------------------------------------------------
# CRAWL / RESEARCH / ATTACHMENT ENHANCEMENTS
# ----------------------------------------------------------

@mcp.tool()
def log_crawl(
    url: str,
    http_status: int = 200,
    content_hash: str = "",
    notes: str = "",
) -> Dict[str, Any]:
    """
    Record or update a crawl entry so the agent can avoid re-crawling the same URL.
    """
    if not url:
        return err("missing_url")
    sql = (
        "INSERT INTO crawl_log (url, http_status, content_hash, notes) "
        "VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (url) DO UPDATE SET "
        "last_seen = NOW(), "
        "http_status = EXCLUDED.http_status, "
        "content_hash = EXCLUDED.content_hash, "
        "notes = EXCLUDED.notes;"
    )
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (url, http_status, content_hash or None, notes or None))
    return ok({"url": url})


@mcp.tool()
def get_unprocessed_crawls(limit: int = 20) -> Dict[str, Any]:
    """
    Return crawl_log rows that are not yet processed/analysed.
    """
    limit = max(1, min(limit, 200))
    sql = (
        "SELECT * "
        "FROM crawl_log "
        "WHERE processed = FALSE "
        "ORDER BY first_seen ASC "
        "LIMIT %s;"
    )
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (limit,))
        rows = cur.fetchall()
    return ok({"count": len(rows), "crawls": rows})


@mcp.tool()
def mark_crawl_processed(url: str) -> Dict[str, Any]:
    """
    Mark a given URL as processed in crawl_log.
    """
    if not url:
        return err("missing_url")
    sql = "UPDATE crawl_log SET processed = TRUE WHERE url = %s;"
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (url,))
    return ok({"url": url, "processed": True})


@mcp.tool()
def set_person_verified(person_id: str, verified: bool = True) -> Dict[str, Any]:
    """
    Set the verified flag on a person.
    """
    if not person_id:
        return err("missing_person_id")
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE persons SET verified = %s WHERE person_id = %s",
            (verified, person_id),
        )
    return ok({"person_id": person_id, "verified": verified})


@mcp.tool()
def set_person_status(
    person_id: str,
    status: str,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Update research_status and optional research_notes for a person.
    """
    if not person_id:
        return err("missing_person_id")
    if not status:
        return err("missing_status")
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE persons SET research_status = %s, research_notes = %s WHERE person_id = %s",
            (status, notes or None, person_id),
        )
    return ok({"person_id": person_id, "status": status})


@mcp.tool()
def add_attachment_metadata(
    person_id: str = "",
    source_id: str = "",
    download_url: str = "",
    description: str = "",
    should_fetch: bool = False,
) -> Dict[str, Any]:
    """
    Register an attachment by URL only. The file is downloaded later.
    """
    if not download_url:
        return err("missing_download_url")
    att_id = str(uuid.uuid4())
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO attachments (
                attachment_id, person_id, source_id,
                download_url, description, should_fetch
            )
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (
                att_id,
                person_id or None,
                source_id or None,
                download_url,
                description or None,
                should_fetch,
            ),
        )
    return ok({"attachment_id": att_id})


@mcp.tool()
def fetch_attachments_for_person(person_id: str) -> Dict[str, Any]:
    """
    Download all attachments for a person that are marked should_fetch but not fetched.

    Files are saved under /attachments in the container. Make sure this path is
    bind-mounted to a host directory.
    """
    if not person_id:
        return err("missing_person_id")
    base_path = Path("/attachments")
    base_path.mkdir(exist_ok=True)
    results: List[Dict[str, Any]] = []
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT attachment_id, download_url
            FROM attachments
            WHERE person_id = %s
              AND should_fetch = TRUE
              AND fetched = FALSE
              AND download_url IS NOT NULL
            """,
            (person_id,),
        )
        rows = cur.fetchall()
        for row in rows:
            att_id = row["attachment_id"]
            url = row["download_url"]
            try:
                resp = requests.get(url, timeout=20)
                if resp.status_code != 200:
                    results.append(
                        {
                            "attachment_id": att_id,
                            "error": f"http_status={resp.status_code}",
                        }
                    )
                    continue
                filename = f"{att_id}.bin"
                filepath = base_path / filename
                filepath.write_bytes(resp.content)
                cur.execute(
                    """
                    UPDATE attachments
                    SET file_path = %s,
                        file_type = 'binary',
                        fetched = TRUE
                    WHERE attachment_id = %s
                    """,
                    (str(filepath), att_id),
                )
                results.append(
                    {
                        "attachment_id": att_id,
                        "saved_path": str(filepath),
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "attachment_id": att_id,
                        "error": str(e),
                    }
                )
    return ok({"person_id": person_id, "results": results})


# ----------------------------------------------------------
# RELATIONSHIPS / DUPLICATES
# ----------------------------------------------------------

@mcp.tool()
def add_relationship(
    person_id_a: str,
    person_id_b: str,
    relation_type: str,
    confidence_score: float = 1.0,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Create a relationship record between two persons.
    relation_type: parent | child | spouse | sibling | partner | unknown
    """
    if not person_id_a or not person_id_b:
        return err("missing_person_ids")
    if not relation_type:
        return err("missing_relation_type")

    rid = str(uuid.uuid4())
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO relationships (
                relationship_id,
                person_id_a,
                person_id_b,
                relation_type,
                confidence_score,
                notes
            ) VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (rid, person_id_a, person_id_b, relation_type, confidence_score, notes or None),
        )

    return ok({"relationship_id": rid})


@mcp.tool()
def get_person_relationships(person_id: str) -> Dict[str, Any]:
    """
    Return all relationships involving the given person (both as A and B).
    """
    if not person_id:
        return err("missing_person_id")

    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT *
            FROM relationships
            WHERE person_id_a = %s OR person_id_b = %s
            """,
            (person_id, person_id),
        )
        rows = cur.fetchall()

    return ok({"count": len(rows), "relationships": rows})


@mcp.tool()
def set_possible_duplicate_of(
    person_id: str,
    duplicate_of: str,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Mark a person as a likely duplicate of another.
    This does not merge records; it just links them.
    """
    if not person_id or not duplicate_of:
        return err("missing_person_id")

    extra_note = ""
    if notes:
        extra_note = f"\n[Possible duplicate noted] {notes}"

    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE persons
            SET possible_duplicate_of = %s,
                research_notes = COALESCE(research_notes, '') || %s
            WHERE person_id = %s
            """,
            (duplicate_of, extra_note, person_id),
        )

    return ok({"person_id": person_id, "duplicate_of": duplicate_of})


# ----------------------------------------------------------
# ASGI APP
# ----------------------------------------------------------

app = mcp.streamable_http_app()

