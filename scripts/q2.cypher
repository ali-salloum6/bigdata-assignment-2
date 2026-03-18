// Q2: Top personalized product recommendations (Memgraph/Neo4j)

// Part A: Top products for a sample user by weighted interaction
MATCH (u:User)-[r:PERFORMED]->(p:Product)
WITH u, p,
     SUM(CASE r.event_type
         WHEN 'purchase' THEN 5
         WHEN 'cart' THEN 3
         WHEN 'view' THEN 1
         ELSE 0
     END) AS score
ORDER BY score DESC
WITH u, COLLECT({product_id: p.product_id, score: score})[..10] AS top_products
LIMIT 1
RETURN u.user_id AS user_id, top_products;

// Part B: Collaborative filtering — friend-purchased products
MATCH (u:User)-[:FRIENDS_WITH]-(friend:User)-[r:PERFORMED {event_type: 'purchase'}]->(p:Product)
WHERE NOT EXISTS { MATCH (u)-[:PERFORMED {event_type: 'purchase'}]->(p) }
WITH u, p, COUNT(DISTINCT friend) AS friend_count
ORDER BY friend_count DESC
WITH u, COLLECT({product_id: p.product_id, friend_count: friend_count})[..10] AS recs
LIMIT 1
RETURN u.user_id AS user_id, recs;

// Part C: Global top products by weighted score
MATCH (u:User)-[r:PERFORMED]->(p:Product)
WHERE p.category_id <> 0
WITH p,
     SUM(CASE r.event_type
         WHEN 'purchase' THEN 5
         WHEN 'cart' THEN 3
         WHEN 'view' THEN 1
         ELSE 0
     END) AS total_score,
     COUNT(DISTINCT u) AS unique_users
RETURN p.product_id AS product_id, total_score, unique_users
ORDER BY total_score DESC
LIMIT 20;
