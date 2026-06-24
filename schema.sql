-- Active: 1761214382970@@127.0.0.1@3306@sustaincity_db
-- Active: 1761214382970@@127.0.0.1@3306@cityfix_db
CREATE DATABASE IF NOT EXISTS sustaincity_db;
USE sustaincity_db;

-- 1. Create Departments Table
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dept_username VARCHAR(50) UNIQUE NOT NULL,
    dept_password VARCHAR(255) NOT NULL, 
    dept_name VARCHAR(100) NOT NULL
);

-- Seed core Indian Municipal Departments with starting credentials
INSERT INTO departments (dept_username, dept_password, dept_name) VALUES
('roads_admin', 'roads2026', 'Potholes & Roads'),
('water_admin', 'water2026', 'Water Supply & Sewage'),
('sanitation_admin', 'clean2026', 'Garbage & Sanitation'),
('electric_admin', 'power2026', 'Streetlights & Electricity');

-- 2. Create New Clean Complaints Table
CREATE TABLE complaints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image_filename VARCHAR(255) NOT NULL,
    full_address TEXT NULL,
    latitude DECIMAL(10, 8) NULL,
    longitude DECIMAL(11, 8) NULL,
    detected_issue VARCHAR(100) NOT NULL,
    confidence_score INT NOT NULL,
    severity ENUM('Low', 'Medium', 'High') NOT NULL,
    assigned_department_id INT, 
    complaint_abstract TEXT NOT NULL,
    status ENUM('Pending', 'Assigned', 'In Progress', 'Resolved') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_department_id) REFERENCES departments(id) ON DELETE SET NULL
);

