import os
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

from src.config import GROQ_API_KEY


@tool
def list_desktop_files() -> str:
    """Lists files on the user's desktop."""
    return "file1.txt, secret_plan.pdf, cool_image.png"

tools = [list_desktop_files]

#(Llama 3)
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama3-70b-8192", 
    temperature=0
)


os_agent = create_react_agent(llm, tools=tools)

class OSAgentSystem:
    def __init__(self):
        self.agent = os_agent
        self.config = {"configurable": {"thread_id": "session_1"}} # For memory tracking

    def process_command(self, user_input: str) -> str:
        """Processes a user command through LangGraph and returns the final string response."""
        inputs = {"messages": [("user", user_input)]}
        

        try:
            result = self.agent.invoke(inputs, config=self.config)

            return result["messages"][-1].content
        except Exception as e:
            return f"Error processing command: {str(e)}"

if __name__ == "__main__":

    system = OSAgentSystem()
    print("Testing Agent...")
    print("User: What files are on my desktop?")
    

    if GROQ_API_KEY:
        response = system.process_command("What files are on my desktop?")
        print(f"Agent: {response}")
    else:
        print("Agent: Please set your GROQ_API_KEY in the .env file first!")
