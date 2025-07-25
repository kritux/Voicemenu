import json
from dotenv import load_dotenv
load_dotenv()
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.schema import Document

# 1. Cargar menú desde JSON
with open('menu.json', 'r', encoding='utf-8') as f:
    menu_data = json.load(f)

docs = []
for item in menu_data['menu']:
    if item['category'] == 'pizza':
        extra = []
        if item.get('vegetarian', False):
            extra.append("This pizza is vegetarian. Suitable for vegetarians. Contains no meat. Meat-free option. Perfect for vegetarians and people who do not eat meat.")
        else:
            extra.append("This pizza contains meat. Not vegetarian. Contains animal protein.")
        if item['flavor'].lower() == 'pepperoni':
            extra.append("Recommended for meat lovers. Most popular pizza. Customer favorite. Classic American pizza. Spicy pepperoni slices. Best seller.")
        if item['flavor'].lower() == 'cheese':
            extra.append("Cheese pizza is the cheapest pizza. Simple and classic. Best for kids. Vegetarian option. No meat.")
        if item['flavor'].lower() == 'hawaiian':
            extra.append("Hawaiian pizza contains ham and pineapple. Not vegetarian. Sweet and savory. Contains pork. Tropical flavor.")
        # Frases sobre tamaños
        extra.append("Available sizes: small, medium, large. You can order any pizza in small, medium, or large size. Choose your size: small, medium, or large.")
        extra.append("Small pizza is the cheapest. Large pizza is the biggest. Medium is the standard size.")
        text = (
            f"{item['flavor']} pizza. Sizes: {', '.join(item['sizes'])}. "
            f"{item['description']} "
            f"Prices: " + ", ".join([f"{size}: ${price}" for size, price in item['price'].items()]) + ". "
            + " ".join(extra)
        )
        meta = {
            "category": "pizza",
            "flavor": item['flavor'],
            "sizes": ', '.join(item['sizes']),
            "price": str(item['price'])
        }
    else:
        # Frases y sinónimos para bebidas
        drink_synonyms = {
            "soda": ["soda", "soft drink", "pop", "cola", "refreshing soda", "carbonated drink", "cold drink"],
            "water": ["water", "bottled water", "still water", "plain water", "refreshing water"],
            "wine": ["wine", "glass of wine", "red wine", "white wine", "alcoholic drink", "wine by the glass"]
        }
        synonyms = drink_synonyms.get(item['name'].lower(), [item['name']])
        text = (
            f"{item['name']} ({item['category']}): {item['description']}. Price: ${item['price']}. "
            f"We offer drinks: soda, water, wine. "
            f"{' '.join(synonyms)}. You can order {item['name']} with your pizza. Drinks menu includes {', '.join(drink_synonyms.keys())}. "
            f"Order a {item['name']} to go with your meal."
        )
        meta = {
            "category": item['category'],
            "name": item['name'],
            "price": str(item['price'])
        }
    docs.append(Document(page_content=text, metadata=meta))

# 2. Crear embeddings y almacenar en ChromaDB
vectorstore = Chroma.from_documents(
    docs,
    embedding=OpenAIEmbeddings(),
    persist_directory="./chroma_db"
)
vectorstore.persist()

print("¡Menú cargado exitosamente en ChromaDB!")