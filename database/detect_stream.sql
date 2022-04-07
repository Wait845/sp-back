CREATE TABLE detect_stream (
    id INT PRIMARY KEY AUTO_INCREMENT,
    interface VARCHAR(32) NOT NULL,
    addr VARCHAR(64) NOT NULL,
    target VARCHAR(128) DEFAULT NULL,
    manuf VARCHAR(128) DEFAULT NULL,
    rssi INT NOT NULL,
    frequency INT NOT NULL,
    channel INT NOT NULL,
    timestamp TIMESTAMP(6) NOT NULL,
    probe_type VARCHAR(32) NOT NULL,
    distance double NOT NULL
);