# User Session Tracking Implementation

## Problem
The application needed a way to record user activity metrics, specifically:
- When a user logs in.
- How much time they spend on each session.

## Solution
We implemented a database-backed session tracking system.

### 1. Database Schema
We added a new table `user_sessions` to store session data.
```sql
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 2. Backend Logic (`src/app.py`)
- **Login**: Upon successful authentication, a new row is inserted into `user_sessions`. The generated `session_id` is stored in the user's Flask session.
- **Logout**: When the user logs out, the application retrieves the `session_id` and updates the `logout_time` for that record.

### 3. Migration
Created a script `src/update_db.py` to check for and create the table if it's missing, ensuring smooth deployment.
