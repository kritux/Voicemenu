import os

# Create .env file with OpenAI API key
env_content = """OPENAI_API_KEY=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
"""

with open('.env', 'w') as f:
    f.write(env_content)

print("✅ .env file created successfully!")
print("You can now run the RAG system.") 