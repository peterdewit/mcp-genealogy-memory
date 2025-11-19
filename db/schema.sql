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
    updated_at TIMESTAMP DEFAULT NOW()
);

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
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE events (
    event_id UUID PRIMARY KEY,
    person_id UUID REFERENCES persons(person_id) ON DELETE CASCADE,
    event_type TEXT,
    date_literal TEXT,
    year INT,
    month INT,
    day INT,
    place TEXT,
    country TEXT,
    source_id UUID REFERENCES sources(source_id),
    notes TEXT
);

CREATE TABLE professions (
    profession_id UUID PRIMARY KEY,
    person_id UUID REFERENCES persons(person_id) ON DELETE CASCADE,
    title TEXT,
    start_year INT,
    end_year INT,
    location TEXT,
    source_id UUID REFERENCES sources(source_id),
    notes TEXT
);

CREATE TABLE addresses (
    address_id UUID PRIMARY KEY,
    person_id UUID REFERENCES persons(person_id) ON DELETE CASCADE,
    street TEXT,
    house_number TEXT,
    city TEXT,
    province TEXT,
    country TEXT,
    start_year INT,
    end_year INT,
    source_id UUID REFERENCES sources(source_id),
    notes TEXT
);

CREATE TABLE attachments (
    attachment_id UUID PRIMARY KEY,
    source_id UUID REFERENCES sources(source_id),
    person_id UUID REFERENCES persons(person_id),
    file_name TEXT,
    file_type TEXT,
    file_path TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE comments (
    comment_id UUID PRIMARY KEY,
    person_id UUID REFERENCES persons(person_id),
    source_id UUID REFERENCES sources(source_id),
    author TEXT,
    text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_persons_name ON persons (surname, given_name);
CREATE INDEX idx_events_person ON events (person_id);
CREATE INDEX idx_professions_person ON professions (person_id);
CREATE INDEX idx_addresses_person ON addresses (person_id);
