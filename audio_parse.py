import openai
import json

SYSTEM_PROMPT = """
Eres un asistente de órdenes para un restaurante de delivery. 
Recibes una transcripción de voz del cliente y tu trabajo es:
1) Identificar artículos del menú y sus cantidades.
2) Si el cliente no dice cantidad, asumir 1.
3) Devolver siempre un JSON con:
   {
     "items": [
       {"name": "<nombre del ítem>", "quantity": <número>},
       ...
     ]
   }
No incluyas texto adicional ni explicación.
"""

def parse_order_with_ai(transcript: str) -> dict:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Transcripción: \"{transcript}\""}
        ],
        temperature=0
    )
    content = response.choices[0].message.content
    return json.loads(content) 