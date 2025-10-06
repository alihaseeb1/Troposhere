-- Enum-like types (use SQL enums or domain/checks; here I create enums where appropriate) CREATE TYPE global_roles AS ENUM ('superuser','user');

CREATE TYPE club_roles AS ENUM ('admin','moderator','member');

CREATE TYPE item_status AS ENUM ('available','out_of_service');

CREATE TABLE users ( 
    id SERIAL PRIMARY KEY, 
    email TEXT NOT NULL UNIQUE, 
    name TEXT NOT NULL, 
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), 
    provider_id TEXT NOT NULL UNIQUE, 
    provider TEXT NOT NULL, 
    picture TEXT, 
    global_role global_roles NOT NULL DEFAULT 'user' 
);

CREATE TABLE clubs ( 
    id SERIAL PRIMARY KEY, 
    name TEXT NOT NULL UNIQUE, 
    description TEXT, 
    created_at TIMESTAMPTZ NOT NULL DEFAULT now() 
);

CREATE TABLE memberships ( 
    user_id INTEGER NOT NULL, 
    club_id INTEGER NOT NULL, 
    role club_roles NOT NULL DEFAULT 'member', 
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(), 
    PRIMARY KEY (user_id, club_id), CONSTRAINT fk_memberships_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE, 
    CONSTRAINT fk_memberships_club FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE CASCADE, 
    CONSTRAINT uix_user_club UNIQUE (user_id, club_id) 
);

CREATE TABLE items ( 
    id SERIAL PRIMARY KEY, 
    name TEXT NOT NULL, 
    description TEXT, 
    club_id INTEGER, 
    is_high_risk BOOLEAN NOT NULL DEFAULT false, 
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), 
    status item_status NOT NULL DEFAULT 'available', 
    CONSTRAINT fk_items_club FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE SET NULL 
);

CREATE INDEX idx_items_club_id ON items (club_id);