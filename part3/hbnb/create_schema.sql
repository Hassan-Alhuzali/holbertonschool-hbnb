-- HBnB schema creation script (SQLite)
-- Creates tables for users, places, reviews, amenities and the association table.

PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- Base columns are present on every table: id, created_at, updated_at

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT,
    is_admin INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS places (
    id TEXT PRIMARY KEY NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    price REAL NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    owner_id TEXT NOT NULL,
    FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
    text TEXT NOT NULL,
    rating INTEGER NOT NULL,
    place_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    FOREIGN KEY(place_id) REFERENCES places(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS amenities (
    id TEXT PRIMARY KEY NOT NULL,
    created_at DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
    name TEXT NOT NULL
);

-- Association table for many-to-many Place <-> Amenity
CREATE TABLE IF NOT EXISTS place_amenity (
    place_id TEXT NOT NULL,
    amenity_id TEXT NOT NULL,
    PRIMARY KEY(place_id, amenity_id),
    FOREIGN KEY(place_id) REFERENCES places(id) ON DELETE CASCADE,
    FOREIGN KEY(amenity_id) REFERENCES amenities(id) ON DELETE CASCADE
);

COMMIT;
