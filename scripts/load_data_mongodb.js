// MongoDB data loader (mongosh) for Big Data Assignment 2.
// Usage: mongosh --file scripts/load_data_mongodb.js
// NOTE: The Python loader (load_data_mongodb.py) is recommended for large files.
// This script provides grader-compatible mongosh loading.

const DB_NAME = 'ecommerce';
const DATA_DIR = '/hostdata/cleaned';

db = db.getSiblingDB(DB_NAME);

function loadCSV(collectionName, filename, indexes) {
    print(`Loading ${collectionName}...`);
    db[collectionName].drop();

    const lines = cat(`${DATA_DIR}/${filename}`).split('\n');
    const headers = lines[0].split(',');
    let batch = [];
    let count = 0;

    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;

        const values = line.split(',');
        const doc = {};
        for (let j = 0; j < headers.length; j++) {
            const val = values[j] || '';
            if (val === '' || val === 'NaT') {
                doc[headers[j]] = null;
            } else if (val === 'True' || val === 'true') {
                doc[headers[j]] = true;
            } else if (val === 'False' || val === 'false') {
                doc[headers[j]] = false;
            } else if (!isNaN(val) && val !== '') {
                doc[headers[j]] = Number(val);
            } else {
                doc[headers[j]] = val;
            }
        }
        batch.push(doc);
        count++;

        if (batch.length >= 5000) {
            db[collectionName].insertMany(batch);
            batch = [];
        }
    }
    if (batch.length > 0) {
        db[collectionName].insertMany(batch);
    }

    if (indexes) {
        indexes.forEach(idx => {
            db[collectionName].createIndex(idx);
        });
    }

    print(`  ${collectionName}: ${db[collectionName].countDocuments()} docs`);
}

loadCSV('events', 'events.csv', [
    { user_id: 1 },
    { product_id: 1 },
    { event_type: 1 }
]);

loadCSV('campaigns', 'campaigns.csv', [
    { id: 1, campaign_type: 1 }
]);

loadCSV('messages', 'messages.csv', [
    { client_id: 1 },
    { campaign_id: 1, message_type: 1 },
    { is_purchased: 1 }
]);

loadCSV('client_first_purchase', 'client_first_purchase_date.csv', [
    { client_id: 1 },
    { user_id: 1 }
]);

loadCSV('friends', 'friends.csv', [
    { friend1: 1 },
    { friend2: 1 }
]);

print('MongoDB loading complete.');
