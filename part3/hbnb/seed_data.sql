-- Seed data for HBnB (SQLite)
PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- Insert an administrator user (id values are UUID-like - pick deterministic values for reproducibility)
INSERT INTO users (id, created_at, updated_at, first_name, last_name, email, password, is_admin) VALUES
('00000000-0000-0000-0000-000000000001', datetime('now'), datetime('now'), 'Admin', 'User', 'admin@example.com', NULL, 1);

-- Insert some sample amenities
INSERT INTO amenities (id, created_at, updated_at, name) VALUES
('amenity-0001', datetime('now'), datetime('now'), 'WiFi'),
('amenity-0002', datetime('now'), datetime('now'), 'Air Conditioning'),
('amenity-0003', datetime('now'), datetime('now'), 'Kitchen');

-- Optionally insert a sample place owned by admin and a review
INSERT INTO places (id, created_at, updated_at, title, description, price, latitude, longitude, owner_id) VALUES
('place-0001', datetime('now'), datetime('now'), 'Sample Place', 'A comfortable sample place', 50.0, 40.7128, -74.0060, '00000000-0000-0000-0000-000000000001');

INSERT INTO reviews (id, created_at, updated_at, text, rating, place_id, user_id) VALUES
('review-0001', datetime('now'), datetime('now'), 'Great stay!', 5, 'place-0001', '00000000-0000-0000-0000-000000000001');

-- Associate amenities to the sample place
INSERT INTO place_amenity (place_id, amenity_id) VALUES
('place-0001', 'amenity-0001'),
('place-0001', 'amenity-0002');

COMMIT;
