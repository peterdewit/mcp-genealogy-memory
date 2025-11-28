-- ============================================================
-- Genealogy Memory Database Schema (final unified version)
-- ============================================================

-- Drop tables in dependency-safe order if you are recreating
-- (ONLY if you are ok losing existing data).
-- DROP TABLE IF EXISTS relationships;
-- DROP TABLE IF EXISTS attachments;
-- DROP TABLE IF EXISTS comments;
-- DROP TABLE IF EXISTS events;
-- DROP TABLE IF EXISTS addresses;
-- DROP TABLE IF EXISTS professions;
-- DROP TABLE IF EXISTS sources;
-- DROP TABLE IF EXISTS crawl_log;
-- DROP TABLE IF EXISTS persons;

------------------------------------------------------------
-- PERSONS
------------------------------------------------------------

CREATE TABLE persons (
    person_id UUID PRIMARY KEY,
    given_name TEXT,
    prefix TEXT,
    surname TEXT,
    gender TEXT,
    birth_year_estimate INT,
    death_year_estimate INT,
    notes TEXT,
    full_name_normalized TEXT,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- verification / research
    verified BOOLEAN DEFAULT FALSE,
    research_status TEXT DEFAULT 'unreviewed',
    research_notes TEXT,
    possible_duplicate_of UUID REFERENCES persons(person_id)
);

CREATE INDEX idx_persons_name
    ON persons (surname, given_name);

------------------------------------------------------------
-- CRAWL LOG
------------------------------------------------------------

CREATE TABLE crawl_log (
    crawl_id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    http_status INT,
    content_hash TEXT,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    notes TEXT
);

CREATE INDEX idx_crawl_log_processed
    ON crawl_log(processed);

------------------------------------------------------------
-- SOURCES
------------------------------------------------------------

CREATE TABLE sources (
    source_id UUID PRIMARY KEY,
    source_type TEXT,
    archive_code TEXT,
    archive_name TEXT,
    identifier TEXT,
    url TEXT,
    collection TEXT,
    document_number TEXT,
    registry_number TEXT,
    institution_name TEXT,
    raw_json TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    -- new fields
    image_url TEXT,
    crawl_id BIGINT REFERENCES crawl_log(crawl_id) ON DELETE SET NULL
);

CREATE INDEX idx_sources_url
    ON sources(url);

------------------------------------------------------------
-- EVENTS
------------------------------------------------------------

CREATE TABLE events (
    event_id UUID PRIMARY KEY,
    person_id UUID NOT NULL
        REFERENCES persons(person_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    date_literal TEXT,
    year INT,
    month INT,
    day INT,
    place TEXT,
    country TEXT,
    source_id UUID
        REFERENCES sources(source_id) ON DELETE SET NULL,
    notes TEXT
);

CREATE INDEX idx_events_person
    ON events(person_id);

------------------------------------------------------------
-- PROFESSIONS
------------------------------------------------------------

CREATE TABLE professions (
    profession_id UUID PRIMARY KEY,
    person_id UUID NOT NULL
        REFERENCES persons(person_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    start_year INT,
    end_year INT,
    location TEXT,
    source_id UUID
        REFERENCES sources(source_id) ON DELETE SET NULL,
    notes TEXT
);

CREATE INDEX idx_professions_person
    ON professions(person_id);

------------------------------------------------------------
-- ADDRESSES
------------------------------------------------------------

CREATE TABLE addresses (
    address_id UUID PRIMARY KEY,
    person_id UUID NOT NULL
        REFERENCES persons(person_id) ON DELETE CASCADE,
    street TEXT,
    house_number TEXT,
    city TEXT,
    province TEXT,
    country TEXT,
    start_year INT,
    end_year INT,
    source_id UUID
        REFERENCES sources(source_id) ON DELETE SET NULL,
    notes TEXT
);

CREATE INDEX idx_addresses_person
    ON addresses(person_id);

------------------------------------------------------------
-- COMMENTS
------------------------------------------------------------

CREATE TABLE comments (
    comment_id UUID PRIMARY KEY,
    person_id UUID
        REFERENCES persons(person_id) ON DELETE SET NULL,
    source_id UUID
        REFERENCES sources(source_id) ON DELETE SET NULL,
    author TEXT,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_comments_person
    ON comments(person_id);

------------------------------------------------------------
-- ATTACHMENTS
------------------------------------------------------------

CREATE TABLE attachments (
    attachment_id UUID PRIMARY KEY,
    source_id UUID
        REFERENCES sources(source_id) ON DELETE SET NULL,
    person_id UUID
        REFERENCES persons(person_id) ON DELETE SET NULL,
    file_name TEXT,
    file_type TEXT,
    file_path TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    -- deferred download
    download_url TEXT,
    should_fetch BOOLEAN DEFAULT FALSE,
    fetched BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_attachments_person
    ON attachments(person_id);

CREATE INDEX idx_attachments_fetch
    ON attachments(should_fetch, fetched);

------------------------------------------------------------
-- RELATIONSHIPS
------------------------------------------------------------

CREATE TABLE relationships (
    relationship_id UUID PRIMARY KEY,
    person_id_a UUID NOT NULL
        REFERENCES persons(person_id) ON DELETE CASCADE,
    person_id_b UUID NOT NULL
        REFERENCES persons(person_id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL CHECK (
        relation_type IN (
            'parent',
            'child',
            'spouse',
            'sibling',
            'partner',
            'unknown'
        )
    ),
    confidence_score REAL DEFAULT 1.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_relationships_person_a
    ON relationships(person_id_a);

CREATE INDEX idx_relationships_person_b
    ON relationships(person_id_b);

