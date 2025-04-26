from langchain.chains import ConversationChain as LangchainConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from chatbot.prompts.base_prompts import SYSTEM_PROMPT
import os
from dotenv import load_dotenv

load_dotenv()

class ConversationChain:
    """Wrapper around Langchain ConversationChain for educational CRM interactions"""
    
    def __init__(self, conversation_id=None, llm_model="gpt-4o"):
        self.llm = ChatOpenAI(
            temperature=0.7,
            model=llm_model,
        )
        
        self.memory = ConversationBufferMemory(
            return_messages=True
        )
        
        self.chain = LangchainConversationChain(
            llm=self.llm,
            memory=self.memory,
            verbose=True
        )
        
        self.conversation_id = conversation_id
        
        # Add system prompt to memory
        self.add_message("system", SYSTEM_PROMPT)
    
    def add_message(self, role, content):
        """Add a message to the conversation memory"""
        if role == "user":
            self.memory.chat_memory.add_user_message(content)
        elif role == "assistant":
            self.memory.chat_memory.add_ai_message(content)
        elif role == "system":
            self.memory.chat_memory.add_message({"role": "system", "content": content})
        else:
            raise ValueError(f"Unknown role: {role}")
    
    def get_response(self, user_input):
        """Get a response from the chatbot"""
        return self.chain.predict(input=user_input)
    
    def get_messages(self):
        """Get all messages in the conversation"""
        return self.memory.chat_memory.messages