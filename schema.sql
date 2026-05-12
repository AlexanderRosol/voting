-- =========================================
-- PostgreSQL Voting Application Database
-- =========================================

-- Optional: remove old tables if they exist
DROP TABLE IF EXISTS votes CASCADE;
DROP TABLE IF EXISTS poll_options CASCADE;
DROP TABLE IF EXISTS polls CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- =========================================
-- USERS TABLE
-- =========================================

CREATE TABLE users (
    id INTEGER PRIMARY KEY,

    username VARCHAR(30) NOT NULL UNIQUE,
    email VARCHAR(254) NOT NULL UNIQUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- POLLS TABLE
-- =========================================

CREATE TABLE polls (
    id INTEGER PRIMARY KEY,

    title VARCHAR(120) NOT NULL,
    description TEXT,

    created_by INTEGER NOT NULL,

    status VARCHAR(10) NOT NULL DEFAULT 'active',

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,

    CONSTRAINT fk_polls_user
        FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_poll_status
        CHECK (status IN ('active', 'closed', 'draft'))
);

-- =========================================
-- POLL OPTIONS TABLE
-- =========================================

CREATE TABLE poll_options (
    id INTEGER PRIMARY KEY,

    poll_id INTEGER NOT NULL,

    option_text VARCHAR(100) NOT NULL,

    display_order SMALLINT NOT NULL DEFAULT 1,

    CONSTRAINT fk_options_poll
        FOREIGN KEY (poll_id)
        REFERENCES polls(id)
        ON DELETE CASCADE
);

-- =========================================
-- VOTES TABLE
-- =========================================

CREATE TABLE votes (
    id INTEGER PRIMARY KEY,

    user_id INTEGER NOT NULL,
    poll_id INTEGER NOT NULL,
    option_id INTEGER NOT NULL,

    voted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_votes_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_votes_poll
        FOREIGN KEY (poll_id)
        REFERENCES polls(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_votes_option
        FOREIGN KEY (option_id)
        REFERENCES poll_options(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_votes_user_poll
        UNIQUE (user_id, poll_id)
);

-- =========================================
-- INDEXES
-- =========================================
/*
CREATE INDEX idx_polls_created_by
    ON polls(created_by);

CREATE INDEX idx_poll_options_poll_id
    ON poll_options(poll_id);

CREATE INDEX idx_votes_user_id
    ON votes(user_id);

CREATE INDEX idx_votes_option_id
    ON votes(option_id);
*/