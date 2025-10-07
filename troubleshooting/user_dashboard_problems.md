# User Dashboard Troubleshooting

## 1. Problem: Accuracy graph was not being created

- **Cause:**  
  The DataFrame used for plotting was not grouped by subject. As a result, it lacked the structure needed to compute and display subject-wise accuracy.

- **Fix:**  
  Used the `agg()` function to group the original DataFrame by `subject` and aggregate two key metrics:  
  - `total_attempts` (count of questions attempted)  
  - `correct_answers` (sum of correct responses)  

  Then, calculated a new `accuracy` column using the formula:
  ```python
  accuracy_df['accuracy'] = (accuracy_df['correct_answers'] / accuracy_df['total_questions']) * 100
