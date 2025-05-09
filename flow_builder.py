from openai import OpenAI
import os

def generate_flowchart(transcript):
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    prompt = f"""
    Create a mermaid flowchart based on the following transcript:
    {transcript}
    
    Return only the mermaid flowchart code.
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that creates mermaid flowcharts."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content
