from openai import OpenAI
import re
import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def getChatResponse(prompt:str):
    client = OpenAI()
    completion = client.responses.create(
        model="gpt-4o",
        input=prompt
    )
    return (completion.output_text)

def clean_chat_response(response: str) -> str:
    """
    Args:
        response: Raw response from the model
        
    Returns:
        Cleaned response text
    """
    # Remove <THINK>...</THINK> sections
    cleaned = re.sub(r'<THINK>.*?</THINK>', '', response, flags=re.DOTALL)
    
    # Remove any other tags like <REASONING> if they exist
    cleaned = re.sub(r'<[^>]+>.*?</[^>]+>', '', cleaned, flags=re.DOTALL)
    
    # Remove any remaining HTML-like tags
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    
    # Remove Markdown code block formatting (```json and ```)
    cleaned = re.sub(r'```json\s*', '', cleaned)
    cleaned = re.sub(r'```', '', cleaned)
    
    return cleaned.strip()