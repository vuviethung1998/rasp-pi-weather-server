db.createUser(
        {
            user: "hungvv",
            pwd: "hungvv",
            roles: [
                {
                    role: "readWrite",
                    db: "SENSOR_DATABASE"
                }
            ]
        }
);