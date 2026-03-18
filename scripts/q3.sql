-- Q3: Full-text search for products based on category_code keywords
-- Using PostgreSQL full-text search with tsvector/tsquery and GIN index.

-- Create a text search index on category_code (replace dots with spaces for tokenization)
CREATE INDEX IF NOT EXISTS idx_events_fts_category
ON events USING GIN (to_tsvector('english', REPLACE(category_code, '.', ' ')));

-- Search for products matching keyword 'electronics' in category_code
SELECT DISTINCT
    product_id,
    category_code,
    brand,
    price
FROM events
WHERE to_tsvector('english', REPLACE(category_code, '.', ' '))
      @@ to_tsquery('english', 'electronics')
ORDER BY product_id
LIMIT 20;

-- Search for products matching 'kitchen' keyword
SELECT DISTINCT
    product_id,
    category_code,
    brand,
    price
FROM events
WHERE to_tsvector('english', REPLACE(category_code, '.', ' '))
      @@ to_tsquery('english', 'kitchen')
ORDER BY product_id
LIMIT 20;

-- Search combining multiple keywords with AND
SELECT DISTINCT
    product_id,
    category_code,
    brand,
    price
FROM events
WHERE to_tsvector('english', REPLACE(category_code, '.', ' '))
      @@ to_tsquery('english', 'appliances & kitchen')
ORDER BY product_id
LIMIT 20;
