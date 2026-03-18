-- Q1: Campaign effectiveness on purchases
-- Analyze whether campaigns attracted customers to purchase products.
-- Join messages with campaigns, compute purchase rate per campaign type/channel,
-- and identify social network influence via the friends table.

-- Part A: Purchase rate by campaign type and channel
SELECT
    c.campaign_type,
    c.channel,
    COUNT(m.id) AS total_messages,
    SUM(CASE WHEN m.is_purchased THEN 1 ELSE 0 END) AS purchases,
    ROUND(
        100.0 * SUM(CASE WHEN m.is_purchased THEN 1 ELSE 0 END) / NULLIF(COUNT(m.id), 0),
        2
    ) AS purchase_rate_pct
FROM messages m
JOIN campaigns c ON c.id = m.campaign_id AND c.campaign_type = m.message_type
GROUP BY c.campaign_type, c.channel
ORDER BY purchase_rate_pct DESC;

-- Part B: Top 10 campaigns by purchase conversion
SELECT
    c.id AS campaign_id,
    c.campaign_type,
    c.channel,
    c.topic,
    COUNT(m.id) AS total_messages,
    SUM(CASE WHEN m.is_purchased THEN 1 ELSE 0 END) AS purchases,
    ROUND(
        100.0 * SUM(CASE WHEN m.is_purchased THEN 1 ELSE 0 END) / NULLIF(COUNT(m.id), 0),
        2
    ) AS purchase_rate_pct
FROM messages m
JOIN campaigns c ON c.id = m.campaign_id AND c.campaign_type = m.message_type
GROUP BY c.id, c.campaign_type, c.channel, c.topic
HAVING COUNT(m.id) >= 100
ORDER BY purchase_rate_pct DESC
LIMIT 10;

-- Part C: Social influence — do users with purchasing friends buy more from campaigns?
WITH purchasers AS (
    SELECT DISTINCT m.user_id
    FROM messages m
    WHERE m.is_purchased = TRUE
),
friend_purchasers AS (
    SELECT f.friend1 AS user_id, COUNT(DISTINCT f.friend2) AS purchasing_friends
    FROM friends f
    JOIN purchasers p ON f.friend2 = p.user_id
    GROUP BY f.friend1
)
SELECT
    CASE
        WHEN fp.purchasing_friends IS NULL THEN '0 purchasing friends'
        WHEN fp.purchasing_friends BETWEEN 1 AND 5 THEN '1-5 purchasing friends'
        ELSE '6+ purchasing friends'
    END AS friend_group,
    COUNT(DISTINCT m.user_id) AS users,
    ROUND(
        100.0 * SUM(CASE WHEN m.is_purchased THEN 1 ELSE 0 END) / NULLIF(COUNT(m.id), 0),
        2
    ) AS purchase_rate_pct
FROM messages m
LEFT JOIN friend_purchasers fp ON m.user_id = fp.user_id
GROUP BY friend_group
ORDER BY purchase_rate_pct DESC;
