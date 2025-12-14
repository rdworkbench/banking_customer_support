-- db/schema.sql

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id      TEXT PRIMARY KEY,              -- 6-digit ID (e.g., "123456")
    customer_name  TEXT,                          -- optional, may be NULL
    message        TEXT NOT NULL,                 -- original feedback / complaint
    status         TEXT NOT NULL DEFAULT 'Open',  -- Open / In Progress / Resolved
    correlation_id TEXT,                          -- Transaction ID for Ops
    created_at     TEXT NOT NULL,                 -- ISO datetime string
    updated_at     TEXT NOT NULL                  -- ISO datetime string
);
