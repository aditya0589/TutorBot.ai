Settings Feature Documentation
Overview
The settings feature in the TutorBot.ai application allows users to manage their account details, including changing their username, updating their password, and deleting their account permanently. This feature is accessible via the /settings route and is designed to provide a secure and user-friendly interface for account management. The implementation evolved through multiple iterations to address initial limitations and enhance functionality.
Implementation Details
Initial Setup
The settings functionality began with a basic Flask route and form setup using Flask-WTF. The initial SettingsForm included fields for:

current_password (required for verification)
new_username (required for updates)
new_password and confirm_password (required for password changes)
delete_account (a checkbox for account deletion)

The /settings route handled form submission, validating the current password against the stored hash using bcrypt, and updating the users table in the MySQL database accordingly. Account deletion was initially tied to the same form submission, deleting associated records from user_notes and quiz_attempts tables.
Evolution of Functionality

Flexible Updates:

Initially, the form required both new_username and new_password to be filled for any update, which was restrictive. I modified the SettingsForm by removing DataRequired() from new_username and new_password, making them optional.
In the /settings route, I introduced dynamic SQL query construction using update_query and update_params to update only the fields provided (e.g., username only, password only, or both), while still requiring current_password for verification.


Account Deletion Enhancement:

The original checkbox-based deletion was replaced with a dedicated "Delete Account Permanently" button to improve user experience and security.
A new /delete_account POST endpoint was created to handle deletion separately. JavaScript was added to the settings.html template to trigger a confirmation dialog ("Deleting account permanently") and send a fetch request with the current password.
The endpoint verifies the password, deletes all associated data, clears the session, and redirects to the index page.


CSS and Styling:

Initially, the page relied on Bootstrap for styling. I removed Bootstrap dependencies to align with the project’s custom dark blue theme (#0a192f, #112240, #1e2a44, #00aaff), recreating styles inline to match other pages like quiz.html and subjects.html.



Code Structure

app.py:
The /settings route processes form data and updates the database conditionally.
The /delete_account route handles deletion with password verification.


settings.html:
Contains the form with input fields, a "Save Changes" button, and a "Delete Account Permanently" button.
Includes JavaScript for the deletion confirmation and fetch request.


CSS:
Custom styles define the dark theme, form layouts, and button behaviors, ensuring consistency across the application.



Problems Faced and Solutions
1. Mandatory Field Requirement

Problem: The initial implementation required both new_username and new_password to be filled, forcing users to change both even if they only wanted one.
Solution: Removed DataRequired() validators and implemented conditional updates in the /settings route, checking which fields were provided before constructing the SQL query. This allowed independent updates.

2. Deletion Logic Integration

Problem: The checkbox-based deletion was part of the main form, risking accidental deletion if the form was submitted with the box checked unintentionally.
Solution: Separated deletion into a button-triggered action with a confirmation dialog. The new /delete_account endpoint ensured password verification, reducing the risk of unintended deletions.

3. JavaScript Fetch Mismatch

Problem: The fetch request in settings.html expected a JSON response, but the /delete_account endpoint returned a 302 redirect with a flash message, causing the .then(response => response.json()) to fail. This led to logs showing POST /delete_account 302 followed by an unexpected GET /login 200.
Solution: Updated the JavaScript to handle redirects directly with if (response.redirected) { window.location.href = response.url; }, relying on Flask’s redirect behavior to display flash messages.

4. Styling Inconsistency

Problem: Reliance on Bootstrap created a dependency and stylistic mismatch with the custom dark theme used elsewhere.
Solution: Removed Bootstrap, recreated styles inline, and aligned them with the project’s color scheme and layout, ensuring a cohesive look across all pages.

5. Debugging Challenges

Problem: Identifying why deletion redirected to /login instead of /settings on error required extensive log analysis.
Solution: Added debug print statements in the /delete_account route to trace password verification and deletion steps, helping confirm the issue was the JavaScript response handling.

Lessons Learned

Flexibility in Form Design: Making fields optional improved user control, but required careful validation and query construction.
Security Considerations: Separating deletion into a confirmed action enhanced security, highlighting the importance of user intent verification.
Frontend-Backend Sync: Mismatches between JavaScript expectations and server responses underscored the need for aligned communication protocols.
Consistency: Custom styling over frameworks ensured a unified brand identity but required more manual effort.

Future Improvements

CSRF Protection: Add CSRF tokens to the fetch request for security in production.
Error Feedback: Enhance the JavaScript to display server-side flash messages directly on the page without relying solely on redirects.
Database Descriptions: Store subject descriptions in the subjects table to make the subjects.html page more dynamic.
Testing: Implement unit tests for the /settings and /delete_account routes to catch regressions.

This documentation reflects the settings feature’s development as of 09:31 PM IST on August 17, 2025. The iterative process addressed initial limitations, ensuring a robust and user-friendly experience.
