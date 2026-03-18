// Q3: Full-text search for products based on category_code keywords (MongoDB)
// The text index on category_code was already created during data loading.
// Run: mongosh --file scripts/q3.js

db = db.getSiblingDB('ecommerce');

// Search for products matching 'electronics'
print("=== Search: electronics ===");
const r1 = db.events.find(
    { $text: { $search: "electronics" } },
    { score: { $meta: "textScore" }, product_id: 1, category_code: 1, brand: 1, price: 1, _id: 0 }
).sort({ score: { $meta: "textScore" } }).limit(20).toArray();
printjson(r1);

// Search for products matching 'kitchen'
print("\n=== Search: kitchen ===");
const r2 = db.events.find(
    { $text: { $search: "kitchen" } },
    { score: { $meta: "textScore" }, product_id: 1, category_code: 1, brand: 1, price: 1, _id: 0 }
).sort({ score: { $meta: "textScore" } }).limit(20).toArray();
printjson(r2);

// Search combining keywords 'appliances kitchen'
print("\n=== Search: appliances kitchen ===");
const r3 = db.events.find(
    { $text: { $search: "\"appliances\" \"kitchen\"" } },
    { score: { $meta: "textScore" }, product_id: 1, category_code: 1, brand: 1, price: 1, _id: 0 }
).sort({ score: { $meta: "textScore" } }).limit(20).toArray();
printjson(r3);
