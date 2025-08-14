# Quiz Generation and Display Process
## Overview
The quiz feature in the TutorBot.ai application is an AI-powered tool that generates and displays multiple-choice questions based on user-selected parameters. This document outlines the process of quiz generation and display, followed by a detailed account of the challenges faced during integration and development.

## Quiz Generation Process
1. **User Input Collection**:
   - The user accesses the `/quiz` route via a GET request, which renders the `quiz.html` template.
   - Through a form, the user selects a subject (e.g., "ml" for Machine Learning), difficulty level (e.g., "beginner"), enters a custom topic (e.g., "Regression"), and chooses the number of questions (e.g., 5).
   - These inputs are submitted via a POST request to the `/quiz` endpoint.

2. **Quiz Data Generation**:
   - The `SubjectTutor` class (from the `tutor` module) is instantiated to handle AI-driven content generation.
   - A query is constructed dynamically, e.g., "Generate 5 multiple-choice questions on ml for beginner level, focusing on Regression. Each question should have a question text, 4 options (a, b, c, d), one correct answer, and a brief explanation of the correct answer. Return the response as a JSON object with a 'questions' array, where each question is an object with 'question', 'options' (array of 4), 'correct_answer' (index 0-3), and 'explanation' (string)."
   - The `tutor.generate_response` method processes this query, leveraging an AI model to produce a raw text response containing a JSON object.

3. **JSON Parsing**:
   - The raw response is parsed to extract the JSON data. A regular expression (`re.search(r'```json\s*(\{.*?\})\s*```', ...)` checks for a JSON code block, or it assumes the response starts with a JSON object if no block is found.
   - The extracted JSON is validated and loaded into a Python dictionary (`quiz_data`) using `json.loads`.
   - The `quiz_data` dictionary, containing a 'questions' array with question objects, is stored in the session (`session['quiz_data']`) for persistence across requests.

4. **Display on Screen**:
   - The parsed `quiz_data` is passed to the `quiz.html` template.
   - The template iterates over the 'questions' array, displaying each question with its text and four options labeled "a)", "b)", "c)", and "d)".
   - A text input field is provided for each question, allowing users to enter their answers (intended as option letters like "a", "b", etc.).
   - The form submits to the `/submit_quiz` endpoint via POST when the user clicks "Submit Answers".

## Problems Faced During Integration and Quiz Development
### 1. **Initial Score Calculation Issue**
   - **Problem**: The quiz always displayed a score of 0 because the comparison logic expected the full option text (e.g., "Predicting a continuous numerical value") while users entered single letters (e.g., "a").
   - **Cause**: The original logic normalized user input by removing prefixes (e.g., "a)") but compared it to the full text, leading to mismatches.
   - **Solution**: Adjusted the scoring to map user-entered letters ("a" to "d") to indices (0 to 3) and compared them with the `correct_answer` index from the JSON.
   - **Impact**: Resolved with a change in the `submit_quiz` function to use `ord(user_answer_cleaned) - ord('a')` for index-based matching.

### 2. **Missing Import Error**
   - **Problem**: A `NameError: name 'time' is not defined` caused a 500 Internal Server Error when submitting the quiz, due to the use of `time.time()` for `quiz_no` without importing the `time` module.
   - **Cause**: The `import time` statement was omitted in the initial code snippet.
   - **Solution**: Added `import time` at the top of `app.py`.
   - **Impact**: Fixed the server error, allowing database insertions to proceed.

### 3. **User Input Format Mismatch**
   - **Problem**: Users entered option letters (e.g., "a") instead of the full text, but the initial design expected full-text answers, leading to incorrect scoring.
   - **Cause**: The template displayed options with "a)" prefixes, suggesting a letter-based selection, while the backend expected text matching.
   - **Solution**: Updated the scoring logic to handle letter inputs by converting them to indices, aligning with the multiple-choice intent.
   - **Impact**: Improved user experience by accepting the intended input format.

### 4. **Database Integration Challenges**
   - **Problem**: Initially, quiz attempts were not logged due to the missing `time` import, and the schema required careful mapping of fields.
   - **Cause**: The `quiz_attempts` table insertion failed because of the runtime error, and field alignment (e.g., `option1` to `option4`) needed to match the JSON structure.
   - **Solution**: Ensured proper field mapping (e.g., `quiz_data['questions'][i]['options'][0]` to `option1`) and fixed the import issue.
   - **Impact**: Successfully logged each question attempt with `user_id`, `quiz_no`, `question`, `options`, `correct_option`, and `user_option`.

### 5. **JSON Parsing Complexity**
   - **Problem**: The AI-generated response sometimes included extraneous text around the JSON, causing parsing failures.
   - **Cause**: The response format varied, with introductory text before the ````json` block, requiring robust extraction logic.
   - **Solution**: Implemented a regular expression to extract the JSON content reliably, with a fallback for direct JSON responses.
   - **Impact**: Ensured consistent quiz data loading despite variable response formats.

### 6. **CSS Theme Consistency**
   - **Problem**: The initial `quiz.html` used a dark gray theme, which didn’t align with the project’s dark blue theme.
   - **Cause**: Inconsistent color schemes across templates (e.g., `#1a1a1a` vs. `#0a192f`).
   - **Solution**: Updated the CSS to use a dark blue palette (`#0a192f`, `#112240`, `#1e2a44`) with blue accents (`#00aaff`), matching other pages.
   - **Impact**: Achieved a cohesive visual design across the application.

### 7. **Option Display Issue**
   - **Problem**: The quiz initially didn’t display options, showing only a textbox for answers.
   - **Cause**: The template logic conditionally rendered options but was incomplete, relying on a single input field.
   - **Solution**: Modified `quiz.html` to loop through the four options and display them with labels, while retaining the textbox.
   - **Impact**: Improved clarity by showing all choices, enhancing the multiple-choice experience.

### Lessons Learned
- **Input Validation**: Clear instructions and robust input handling are critical for user-friendly applications.
- **Dependency Management**: Always ensure all required imports are included to avoid runtime errors.
- **Testing**: Iterative testing with debug prints helped identify and resolve mismatches early.
- **Documentation**: Maintaining detailed logs and documentation (like this file) aids in tracking issues and solutions.

## Future Improvements
- **Quiz History**: Add a page to view past quiz attempts from the `quiz_attempts` table.
- **Input Flexibility**: Allow both letter and full-text inputs with appropriate validation.
- **Error Handling**: Enhance error messages for JSON parsing failures or database issues.
- **UI Enhancements**: Add radio buttons for option selection instead of a textbox to enforce the multiple-choice format.

This documentation reflects the development process as of 07:15 PM IST on August 14, 2025.
