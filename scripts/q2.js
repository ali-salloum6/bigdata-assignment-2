// Q2: Top personalized product recommendations (MongoDB)
// Run: mongosh --file scripts/q2.js

db = db.getSiblingDB('ecommerce');

// Part A: Top recommended products for a sample user (own behavior)
print("=== Part A: Top products for sample user (own behavior) ===");
const sampleUser = db.events.findOne({}, { user_id: 1 });
const userId = sampleUser.user_id;
print("Sample user_id: " + userId);

const partA = db.events.aggregate([
    { $match: { user_id: userId } },
    {
        $group: {
            _id: "$product_id",
            score: {
                $sum: {
                    $switch: {
                        branches: [
                            { case: { $eq: ["$event_type", "purchase"] }, then: 5 },
                            { case: { $eq: ["$event_type", "cart"] }, then: 3 },
                            { case: { $eq: ["$event_type", "view"] }, then: 1 }
                        ],
                        default: 0
                    }
                }
            }
        }
    },
    { $sort: { score: -1 } },
    { $limit: 10 }
]).toArray();
printjson(partA);

// Part C: Global top products by weighted score
print("\n=== Part C: Global top products by weighted score ===");
const partC = db.events.aggregate([
    { $match: { category_code: { $ne: "" } } },
    {
        $group: {
            _id: { product_id: "$product_id", category_code: "$category_code", brand: "$brand" },
            total_score: {
                $sum: {
                    $switch: {
                        branches: [
                            { case: { $eq: ["$event_type", "purchase"] }, then: 5 },
                            { case: { $eq: ["$event_type", "cart"] }, then: 3 },
                            { case: { $eq: ["$event_type", "view"] }, then: 1 }
                        ],
                        default: 0
                    }
                }
            },
            unique_users: { $addToSet: "$user_id" }
        }
    },
    {
        $addFields: { unique_users_count: { $size: "$unique_users" } }
    },
    { $sort: { total_score: -1 } },
    { $limit: 20 },
    {
        $project: {
            _id: 0,
            product_id: "$_id.product_id",
            category_code: "$_id.category_code",
            brand: "$_id.brand",
            total_score: 1,
            unique_users: "$unique_users_count"
        }
    }
]).toArray();
printjson(partC);
