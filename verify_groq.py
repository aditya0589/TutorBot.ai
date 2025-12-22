import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from tutor import SubjectTutor
    print("Successfully imported SubjectTutor")
    
    tutor = SubjectTutor()
    print("Successfully initialized SubjectTutor with Groq")
    
    # Optional: Try to generate a response if API key is present
    # response = tutor.generate_response("dsa", "What is a linked list?")
    # print(f"Response: {response}")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
