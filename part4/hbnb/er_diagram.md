# HBnB ER Diagram (Mermaid.js)


```mermaid
erDiagram
    USERS {
        CHAR(36) id PK "UUID"
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR email UNIQUE
        VARCHAR password
        BOOLEAN is_admin
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    PLACES {
        CHAR(36) id PK
        VARCHAR title
        TEXT description
        DECIMAL(10,2) price
        FLOAT latitude
        FLOAT longitude
        CHAR(36) owner_id FK
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    REVIEWS {
        CHAR(36) id PK
        TEXT text
        INT rating "1..5"
        CHAR(36) user_id FK
        CHAR(36) place_id FK
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    AMENITIES {
        CHAR(36) id PK
        VARCHAR name UNIQUE
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    PLACE_AMENITY {
        CHAR(36) place_id FK
        CHAR(36) amenity_id FK
        PK(place_id, amenity_id)
        TIMESTAMP created_at
    }

    USERS ||--o{ PLACES : "owns"
    PLACES ||--o{ REVIEWS : "has"
    USERS ||--o{ REVIEWS : "writes"

    PLACES }o--o{ AMENITIES : "has"

    PLACES ||--o{ PLACE_AMENITY : "has"
    AMENITIES ||--o{ PLACE_AMENITY : "available_in"
```



