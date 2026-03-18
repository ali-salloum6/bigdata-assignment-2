// Q3: Full-text search for products based on category_code keywords (Memgraph)
// Using CONTAINS for substring matching on category nodes.

// Search for products in 'electronics' categories
MATCH (p:Product)-[:IN_CATEGORY]->(c:Category)
WHERE c.category_code CONTAINS 'electronics'
RETURN DISTINCT p.product_id AS product_id, c.category_code AS category_code, p.brand AS brand
ORDER BY product_id
LIMIT 20;

// Search for products in 'kitchen' categories
MATCH (p:Product)-[:IN_CATEGORY]->(c:Category)
WHERE c.category_code CONTAINS 'kitchen'
RETURN DISTINCT p.product_id AS product_id, c.category_code AS category_code, p.brand AS brand
ORDER BY product_id
LIMIT 20;

// Search combining 'appliances' AND 'kitchen'
MATCH (p:Product)-[:IN_CATEGORY]->(c:Category)
WHERE c.category_code CONTAINS 'appliances' AND c.category_code CONTAINS 'kitchen'
RETURN DISTINCT p.product_id AS product_id, c.category_code AS category_code, p.brand AS brand
ORDER BY product_id
LIMIT 20;
