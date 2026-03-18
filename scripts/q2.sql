-- Q2: Top personalized product recommendations per user
-- Rank products by weighted interaction frequency:
--   purchase=5, cart=3, view=1
-- Also consider what friends purchased (collaborative filtering).

-- Part A: Top 10 recommended products for a sample user based on own behavior
WITH user_product_scores AS (
    SELECT
        user_id,
        product_id,
        SUM(CASE event_type
            WHEN 'purchase' THEN 5
            WHEN 'cart' THEN 3
            WHEN 'view' THEN 1
            ELSE 0
        END) AS score
    FROM events
    GROUP BY user_id, product_id
)
SELECT user_id, product_id, score
FROM user_product_scores
WHERE user_id = (SELECT user_id FROM events LIMIT 1)
ORDER BY score DESC
LIMIT 10;

-- Part B: Collaborative filtering — products purchased by friends but not by the user
WITH sample_user AS (
    SELECT user_id FROM events LIMIT 1
),
user_purchased AS (
    SELECT DISTINCT product_id
    FROM events
    WHERE user_id = (SELECT user_id FROM sample_user)
      AND event_type = 'purchase'
),
friend_purchases AS (
    SELECT e.product_id, COUNT(DISTINCT e.user_id) AS friend_count
    FROM friends f
    JOIN events e ON e.user_id = f.friend2 AND e.event_type = 'purchase'
    WHERE f.friend1 = (SELECT user_id FROM sample_user)
      AND e.product_id NOT IN (SELECT product_id FROM user_purchased)
    GROUP BY e.product_id
)
SELECT product_id, friend_count
FROM friend_purchases
ORDER BY friend_count DESC
LIMIT 10;

-- Part C: Global top products by weighted score
SELECT
    product_id,
    category_code,
    brand,
    SUM(CASE event_type
        WHEN 'purchase' THEN 5
        WHEN 'cart' THEN 3
        WHEN 'view' THEN 1
        ELSE 0
    END) AS total_score,
    COUNT(DISTINCT user_id) AS unique_users
FROM events
WHERE category_code != ''
GROUP BY product_id, category_code, brand
ORDER BY total_score DESC
LIMIT 20;
