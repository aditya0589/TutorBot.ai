--> You will require MySQL for creating the database
--> Database connection details are stored as environment variables

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

CREATE TABLE quiz_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    quiz_no INT NOT NULL,
    question TEXT NOT NULL,
    option1 TEXT,
    option2 TEXT,
    option3 TEXT,
    option4 TEXT,
    correct_option VARCHAR(255),
    user_option VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subjects(
	sub_id INT PRIMARY KEY AUTO_INCREMENT,
    sub_name VARCHAR(50)
);

CREATE TABLE topics(
	topic_id INT PRIMARY KEY AUTO_INCREMENT,
    topic_name VARCHAR(1000),
    weightage INT,
    sub_id INT,
    FOREIGN KEY (sub_id) REFERENCES subjects(sub_id)
);

INSERT INTO subjects(sub_name)
VALUES
('DSA'),
('Computer Networks');

INSERT INTO topics(topic_name, weightage, sub_id)
VALUES
('Time and Space Complexity', 9, 1),
('Recursion and Recurrence Relations', 7, 1),
('Iterative vs Recursive Approaches', 4, 1),
('Arrays', 9, 1),
('Strings', 	7, 1),
('Linked Lists', 8, 1),
('Stacks', 5, 1),
('Queues', 5, 1),
('Trees', 10, 1),
('Heap', 4, 1),
('Hashing', 5, 1),
('Graphs', 10, 1),
('Sorting Algorithms', 5, 1),
('Searching Algorithms', 4, 1),
('Greedy Algorithms', 3, 1),
('Divide & Conquer', 3, 1),
('Dynamic Programming', 6, 1),
('Backtracking', 3, 1),
('String Matching Algorithms', 2, 1);

INSERT INTO topics (topic_name, weightage, sub_id) VALUES
('Network Models (OSI, TCP/IP)', 7, 2),
('Data Transmission (Analog, Digital)', 5, 2),
('Transmission Media (Wired, Wireless)', 5, 2),
('Physical Layer (Signals, Encoding, Multiplexing)', 7, 2),
('Data Link Layer (Error Detection, MAC, ARP)', 8, 2),
('Network Layer (IP Addressing, Subnetting, Routing Algorithms)', 15, 2),
('Transport Layer (TCP, UDP, Congestion Control)', 10, 2),
('Application Layer (HTTP, DNS, SMTP, FTP)', 8, 2),
('Cryptography Basics', 5, 2),
('Network Attacks (DDoS, MITM, Phishing)', 6, 2),
('Firewalls & VPN', 5, 2),
('Cloud Networking', 6, 2),
('Software Defined Networking (SDN)', 6, 2),
('IoT Networking Basics', 7, 2);

CREATE TABLE user_progress(
	user_id INT,
    topic_id INT,
    PRIMARY KEY (user_id, topic_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
);

CREATE TABLE quiz_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    subject VARCHAR(100) NOT NULL, 
    topic VARCHAR(100) NOT NULL,
    quiz_no INT NOT NULL,
    question TEXT NOT NULL,
    option1 TEXT,
    option2 TEXT,
    option3 TEXT,
    option4 TEXT,
    correct_option VARCHAR(255),
    user_option VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
