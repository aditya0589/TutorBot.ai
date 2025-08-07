--> Creation of the database
CREATE DATABASE IF NOT EXISTS tutorbot;
USE tutorbot;
--> Users table to store user details
CREATE TABLE users(id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100), email VARCHAR(100), password VARCHAR(100));

--> table to store the notes
CREATE TABLE user_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    subject VARCHAR(50) NOT NULL,
    note_content TEXT NOT NULL,
    enhanced_note_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
