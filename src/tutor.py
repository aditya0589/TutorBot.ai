from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from config import Config

class SubjectTutor:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=Config.GOOGLE_API_KEY)
        self.memory = {}  # Subject-specific memory
        self.chains = {}  # Subject-specific conversation chains

    def get_chain(self, subject):
        """Get or create a conversation chain for a specific subject."""
        if subject not in self.chains:
            # Define the prompt template with interactive chat support
            template = """You are a highly knowledgeable and professional tutor specializing in {subject}. Your responses should be clear, concise, and educational, written in Markdown format as a single readable paragraph. Maintain a friendly, supportive, and conversational tone. Use the conversation history to provide context-aware answers and allow for follow-up questions. If the query is unclear, politely ask for clarification.

            Current conversation:
            {history}

            User query: {input}
            """
            prompt = PromptTemplate(
                input_variables=["subject", "history", "input"],
                template=template
            )
            # Initialize memory
            memory = ConversationBufferMemory(input_key="input")  # Explicitly set input_key
            self.memory[subject] = memory
            # Create the LLM chain with the prompt and memory
            self.chains[subject] = LLMChain(
                llm=self.llm,
                prompt=prompt,
                memory=memory
            )
        return self.chains[subject]

    def generate_response(self, subject, query):
        """Generate a response based on subject and query, tracking history."""
        chain = self.get_chain(subject)
        # Prepare input dictionary, using only 'input' for memory compatibility
        input_dict = {"input": query, "subject": subject}
        response = chain.invoke(input_dict)
        # Extract and ensure the response is a string, forcing Markdown compatibility
        if isinstance(response, dict):
            response_text = response.get("text", response.get("content", ""))
        else:
            response_text = str(response)
        # Ensure the response is formatted as a single paragraph in Markdown
        if not response_text.strip():
            response_text = "I'm sorry, I couldn't generate a response. Please try again or provide more details."
        elif not response_text.startswith(('#', '-', '`')):
            response_text = f"{response_text}"  # Kept as paragraph
        # Save context manually to maintain chat history
        chain.memory.save_context({"input": query}, {"output": response_text})
        return response_text