from groq import Groq
#import google.generativeai as genai
from dotenv import load_dotenv
import os



load_dotenv()
client = Groq(
    api_key = os.getenv("GROQ_API_KEY")
    )


#genai.configure(api_key=api_key)

#model = genai.GenerativeModel("gemini-2.0-flash")


def generate_email():

    prompt = """
Write a professional cold email for internship opportunities.

Candidate Name: Laksh Vyas

Skills:
- Python
- FastAPI
- AI Agents
- Generative AI
- machine learning
- Data Analysis
- SQL
- Git
- Deep Learning
- Natural Language Processing
- Docker
- Kubernetes
- AWS
- LLMs
- Computer Vision
- RAG
- Lanchain
- Langgraph
- prompt engineering
- DSA
- problem solving
- CN
- OS
- DBMS
- OOPs

Rules:
- Do not use placeholders
- Keep the email concise
- Professional tone
- Mention that my resume is attached
- End the email with Laksh Vyas
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
            'role': 'user',
            'content': prompt
            }
        ]
    )

    return response.choices[0].message.content  