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

-->table for quiz attempts
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

--> table to subjects
CREATE TABLE subjects(
	sub_id INT PRIMARY KEY AUTO_INCREMENT,
    sub_name VARCHAR(50)
);

--> insert into subjects table
INSERT INTO subjects(sub_name)
VALUES
('DSA'),
('Computer Networks'),
('Machine Learning'),
('Database Management Systems'),
('Operating Systems'),
('Web Development');

--> table to store topics
CREATE TABLE topics(
	topic_id INT PRIMARY KEY AUTO_INCREMENT,
    topic_name VARCHAR(50),
    weightage INT,
    sub_id INT,
    FOREIGN KEY (sub_id) REFERENCES subjects(sub_id)
);

--> insert into topics table
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

INSERT INTO topics(topic_name, weightage, sub_id)
VALUES
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

--> insert additional topics for Machine Learning
INSERT INTO topics(topic_name, weightage, sub_id)
VALUES
('Introduction and Types', 4, 3),
('Python Libraries', 6, 3),
('Data Cleaning & Preprocessing', 5, 3),
('Feature Engineering & Scaling', 5, 3),
('Handling Missing Values & Outliers', 5, 3),
('Regression (Linear, Polynomial, Ridge, Lasso)', 10, 3),
('Classification (Logistic Regression, KNN, Decision Trees, Random Forest, SVM)', 15, 3),
('Clustering (K-Means, Hierarchical, DBSCAN)', 8, 3),
('Dimensionality Reduction (PCA, t-SNE)', 7, 3),
('Train/Test Split, Cross-Validation', 4, 3),
('Confusion Matrix, Precision, Recall, F1-Score', 6, 3),
('ROC-AUC Curve', 5, 3),
('Basics of Neural Networks', 8, 3),
('Activation Functions', 5, 3),
('Introduction to TensorFlow/Keras', 7, 3);

--> insert topics for Database Management Systems
INSERT INTO topics(topic_name, weightage, sub_id)
VALUES
('DBMS vs File Systems', 4, 4),
('Data Models (Hierarchical, Network, Relational)', 7, 4),
('ER Model (Entities, Relationships, Attributes, ER Diagrams)', 8, 4),
('Keys (Primary, Foreign, Candidate)', 6, 4),
('Constraints', 5, 4),
('Normalization (1NF, 2NF, 3NF, BCNF)', 10, 4),
('DDL, DML, DCL, TCL Commands', 8, 4),
('Joins (INNER, LEFT, RIGHT, FULL)', 8, 4),
('Subqueries, Views, Indexes', 7, 4),
('Aggregate Functions & Grouping', 5, 4),
('ACID Properties', 5, 4),
('Transaction States', 4, 4),
('Deadlocks & Prevention', 4, 4),
('NoSQL Databases (MongoDB, Redis)', 5, 4),
('Stored Procedures, Triggers', 6, 4),
('Query Optimization', 8, 4);

--> insert topics for Operating Systems
INSERT INTO topics(topic_name, weightage, sub_id)
VALUES
('Functions of OS', 8, 5),
('Types of OS (Batch, Multitasking, Real-Time, Distributed)', 8, 5),
('Process States & Control Block', 8, 5),
('Scheduling Algorithms (FCFS, SJF, RR, Priority)', 15, 5),
('Inter-Process Communication (Pipes, Message Queues, Shared Memory)', 10, 5),
('Paging, Segmentation', 8, 5),
('Virtual Memory, Page Replacement Algorithms', 10, 5),
('File Organization', 6, 5),
('Allocation Methods (Contiguous, Linked, Indexed)', 7, 5),
('Conditions, Prevention, Avoidance (Bankers Algorithm)', 10, 5),
('Interrupts, Device Drivers, Buffering', 10, 5);

--> insert topics for Web Development
INSERT INTO topics(topic_name, weightage, sub_id)
VALUES
('HTML', 8, 6),
('CSS', 8, 6),
('JavaScript', 12, 6),
('Frameworks (React, Vue, Angular — basics)', 10, 6),
('Server-Side Programming (Node.js, Express.js, Flask, Django)', 12, 6),
('REST API Development', 8, 6),
('Authentication & Authorization (JWT, OAuth)', 8, 6),
('SQL & NoSQL Integration', 7, 6),
('CRUD Operations from Web App', 7, 6),
('WebSockets & Real-Time Applications', 6, 6),
('Deployment (Vercel, Netlify, Render, AWS, Heroku)', 7, 6),
('Security (HTTPS, CSRF, XSS, SQL Injection Prevention)', 7, 6);

--> table to store topics toggled by user for progress tracking
CREATE TABLE user_progress(
	user_id INT,
    topic_id INT,
    PRIMARY KEY (user_id, topic_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
);
