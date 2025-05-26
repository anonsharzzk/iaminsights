// MongoDB initialization script
db = db.getSiblingDB('cloud_access');

// Create collections
db.createCollection('users');
db.createCollection('user_access');

// Create indexes for better performance
db.users.createIndex({ "email": 1 }, { unique: true });
db.user_access.createIndex({ "user_email": 1 }, { unique: true });
db.user_access.createIndex({ "data_source": 1 });
db.user_access.createIndex({ "overall_risk_score": -1 });

print("Database initialized successfully");