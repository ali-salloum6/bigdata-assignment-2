// Q1: Campaign effectiveness on purchases (MongoDB)
// Run: mongosh --file scripts/q1.js

db = db.getSiblingDB('ecommerce');

// Part A: Purchase rate by campaign type and channel
print("=== Part A: Purchase rate by campaign type and channel ===");
const partA = db.messages.aggregate([
    {
        $lookup: {
            from: "campaigns",
            let: { cid: "$campaign_id", mtype: "$message_type" },
            pipeline: [
                { $match: { $expr: { $and: [
                    { $eq: ["$id", "$$cid"] },
                    { $eq: ["$campaign_type", "$$mtype"] }
                ]}}}
            ],
            as: "campaign"
        }
    },
    { $unwind: "$campaign" },
    {
        $group: {
            _id: { campaign_type: "$campaign.campaign_type", channel: "$campaign.channel" },
            total_messages: { $sum: 1 },
            purchases: { $sum: { $cond: [{ $eq: ["$is_purchased", "True"] }, 1, 0] } }
        }
    },
    {
        $addFields: {
            purchase_rate_pct: {
                $round: [{ $multiply: [{ $divide: ["$purchases", "$total_messages"] }, 100] }, 2]
            }
        }
    },
    { $sort: { purchase_rate_pct: -1 } }
]).toArray();
printjson(partA);

// Part B: Top 10 campaigns by purchase conversion
print("\n=== Part B: Top 10 campaigns by purchase conversion ===");
const partB = db.messages.aggregate([
    {
        $lookup: {
            from: "campaigns",
            let: { cid: "$campaign_id", mtype: "$message_type" },
            pipeline: [
                { $match: { $expr: { $and: [
                    { $eq: ["$id", "$$cid"] },
                    { $eq: ["$campaign_type", "$$mtype"] }
                ]}}}
            ],
            as: "campaign"
        }
    },
    { $unwind: "$campaign" },
    {
        $group: {
            _id: {
                campaign_id: "$campaign.id",
                campaign_type: "$campaign.campaign_type",
                channel: "$campaign.channel",
                topic: "$campaign.topic"
            },
            total_messages: { $sum: 1 },
            purchases: { $sum: { $cond: [{ $eq: ["$is_purchased", "True"] }, 1, 0] } }
        }
    },
    { $match: { total_messages: { $gte: 100 } } },
    {
        $addFields: {
            purchase_rate_pct: {
                $round: [{ $multiply: [{ $divide: ["$purchases", "$total_messages"] }, 100] }, 2]
            }
        }
    },
    { $sort: { purchase_rate_pct: -1 } },
    { $limit: 10 }
]).toArray();
printjson(partB);
