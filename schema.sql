CREATE DATABASE IF NOT EXISTS reflex_db;

USE reflex_db;

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    role ENUM('Retailer', 'Dispatcher', 'Rider') NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Deliveries (
    delivery_id INT AUTO_INCREMENT PRIMARY KEY,
    retailer_id INT NOT NULL,
    rider_id INT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    delivery_address VARCHAR(255) NOT NULL,
    item_description VARCHAR(255) NOT NULL,
    status ENUM('OPEN', 'ASSIGNED', 'PICKED_UP', 'DELIVERED')
        NOT NULL DEFAULT 'OPEN',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_delivery_retailer
        FOREIGN KEY (retailer_id)
        REFERENCES Users(user_id),

    CONSTRAINT fk_delivery_rider
        FOREIGN KEY (rider_id)
        REFERENCES Users(user_id)
);

CREATE TABLE Status_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    delivery_id INT NOT NULL,
    changed_by INT NOT NULL,
    status ENUM('OPEN', 'ASSIGNED', 'PICKED_UP', 'DELIVERED') NOT NULL,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_history_delivery
        FOREIGN KEY (delivery_id)
        REFERENCES Deliveries(delivery_id),

    CONSTRAINT fk_history_user
        FOREIGN KEY (changed_by)
        REFERENCES Users(user_id)
);

CREATE TABLE QR_confirmations (
    confirmation_id INT AUTO_INCREMENT PRIMARY KEY,
    delivery_id INT NOT NULL,
    qr_code VARCHAR(100) NOT NULL,
    scanned_by INT NOT NULL,
    scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    result ENUM('Successful', 'Failed') NOT NULL,

    CONSTRAINT fk_qr_delivery
        FOREIGN KEY (delivery_id)
        REFERENCES Deliveries(delivery_id),

    CONSTRAINT fk_qr_user
        FOREIGN KEY (scanned_by)
        REFERENCES Users(user_id)
);