// Q1: Campaign effectiveness on purchases (Memgraph/Neo4j)
// Part A: Purchase rate by campaign type and channel
MATCH (u:User)-[:RECEIVED]->(m:Message)-[:BELONGS_TO]->(c:Campaign)
WITH c.campaign_type AS campaign_type, c.channel AS channel,
     COUNT(m) AS total_messages,
     SUM(CASE WHEN m.is_purchased = true THEN 1 ELSE 0 END) AS purchases
RETURN campaign_type, channel, total_messages, purchases,
       toFloat(toInteger(10000.0 * purchases / total_messages)) / 100.0 AS purchase_rate_pct
ORDER BY purchase_rate_pct DESC;

// Part B: Top 10 campaigns by purchase conversion
MATCH (u:User)-[:RECEIVED]->(m:Message)-[:BELONGS_TO]->(c:Campaign)
WITH c.campaign_id AS campaign_id, c.campaign_type AS campaign_type,
     c.channel AS channel, c.topic AS topic,
     COUNT(m) AS total_messages,
     SUM(CASE WHEN m.is_purchased = true THEN 1 ELSE 0 END) AS purchases
WHERE total_messages >= 100
RETURN campaign_id, campaign_type, channel, topic, total_messages, purchases,
       toFloat(toInteger(10000.0 * purchases / total_messages)) / 100.0 AS purchase_rate_pct
ORDER BY purchase_rate_pct DESC
LIMIT 10;

// Part C: Social influence on campaign purchases
MATCH (u:User)-[:RECEIVED]->(m:Message)
OPTIONAL MATCH (u)-[:FRIENDS_WITH]-(friend:User)-[:RECEIVED]->(fm:Message)
WHERE fm.is_purchased = true
WITH u, m,
     COUNT(DISTINCT friend) AS purchasing_friends
WITH
    CASE
        WHEN purchasing_friends = 0 THEN '0 purchasing friends'
        WHEN purchasing_friends <= 5 THEN '1-5 purchasing friends'
        ELSE '6+ purchasing friends'
    END AS friend_group,
    u, m
WITH friend_group,
     COUNT(DISTINCT u) AS users,
     COUNT(m) AS total_messages,
     SUM(CASE WHEN m.is_purchased = true THEN 1 ELSE 0 END) AS purchases
RETURN friend_group, users,
       toFloat(toInteger(10000.0 * purchases / total_messages)) / 100.0 AS purchase_rate_pct
ORDER BY purchase_rate_pct DESC;
