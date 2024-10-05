-- Table: Cards
CREATE TABLE IF NOT EXISTS Cards (
    id VARCHAR(255) PRIMARY KEY,                 -- Unique identifier for the card
    oracle_id VARCHAR(50),                      -- Oracle identifier for the card
    name VARCHAR(255),                          -- Name of the card
    released_at DATE,                           -- Release date of the card
    layout VARCHAR(50),                         -- Layout type of the card
    highres_image BOOLEAN,                      -- Whether a high-resolution image exists (0/1)
    mana_cost VARCHAR(50),                      -- Mana cost (text like {1}{R}{G})
    cmc INT,                                    -- Converted mana cost
    type_line VARCHAR(100),                     -- Type line (creature, instant, etc.)
    oracle_text TEXT(255),                           -- Rules text on the card
    colors VARCHAR(20),                         -- Colors (like [ "R", "G" ])
    color_identity VARCHAR(20),                 -- Color identity (like [ "R", "G" ])
    produced_mana VARCHAR(20),                  -- Mana this card can produce
    rarity VARCHAR(10),                         -- Rarity of the card (common, rare, etc.)
    artist VARCHAR(100),                        -- Artist who illustrated the card
    set_name VARCHAR(100),                      -- Name of the set the card is in
    set_type VARCHAR(50),                       -- Type of set (expansion, core, etc.)
    usd_price DECIMAL(10, 2),                   -- Price in USD
    legalities TEXT(255),                            -- Legalities in various formats (stored as JSON)
    games VARCHAR(50),                          -- Games this card is available in
    image_uri VARCHAR(255)                      -- URL for the image of the card
);

-- -- Index to improve querying by card name
-- CREATE INDEX IF NOT EXISTS idx_name ON Cards(name);

-- -- Index to improve querying by set name
-- CREATE INDEX IF NOT EXISTS idx_set_name ON Cards(set_name);

-- Table: MultiverseIds
-- Since a card can have multiple multiverse IDs, this data should be stored in a separate table
CREATE TABLE IF NOT EXISTS MultiverseIds (
    card_id VARCHAR(255),                       -- Foreign key referencing Cards table
    multiverse_id INTEGER,              -- Multiverse ID
    FOREIGN KEY (card_id) REFERENCES Cards(id)
);

-- Table: Finishes
-- A card can have multiple finishes (foil, nonfoil), so this data should be separated as well
CREATE TABLE IF NOT EXISTS Finishes (
    card_id VARCHAR(255),                       -- Foreign key referencing Cards table
    finish VARCHAR(255),                        -- Finish type (foil, nonfoil, etc.)
    FOREIGN KEY (card_id) REFERENCES Cards(id)
);

-- Table: Keywords
-- A card can have multiple keywords, so this data should be stored separately
CREATE TABLE IF NOT EXISTS Keywords (
    card_id VARCHAR(255),                       -- Foreign key referencing Cards table
    keyword VARCHAR(255),                       -- Keyword ability (if any)
    FOREIGN KEY (card_id) REFERENCES Cards(id)
);

-- Table: Formats
-- A card can be legal or illegal in different formats, so we store format-specific legality
CREATE TABLE IF NOT EXISTS Formats (
    card_id VARCHAR(255),                       -- Foreign key referencing Cards table
    format VARCHAR(255),                        -- Format name (e.g., standard, modern, legacy)
    legality VARCHAR(255),                      -- Legality status (legal, not_legal, restricted, etc.)
    FOREIGN KEY (card_id) REFERENCES Cards(id)
);
