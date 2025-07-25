from flask import Blueprint, request, jsonify, current_app
from dotenv import load_dotenv
import os
import csv
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.schema import Document
import logging

load_dotenv()

rag_bp = Blueprint('rag', __name__)

CHROMA_PATH = os.getenv('RAG_PERSIST_DIR', './chroma_db')

@rag_bp.route('/api/menu/ingest', methods=['POST'])
def ingest_menu():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    # Leer CSV y convertir a documentos
    docs = []
    csvfile = file.stream.read().decode('utf-8').splitlines()
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row['category'] == 'pizza':
            extra = []
            if row.get('vegetarian', '').lower() == 'true':
                extra.append("This pizza is vegetarian. Suitable for vegetarians. Contains no meat. Meat-free option. Perfect for vegetarians and people who do not eat meat.")
            else:
                extra.append("This pizza contains meat. Not vegetarian. Contains animal protein.")
            if row['flavor_or_name'].lower() == 'pepperoni':
                extra.append("Recommended for meat lovers. Most popular pizza. Customer favorite. Classic American pizza. Spicy pepperoni slices. Best seller.")
            if row['flavor_or_name'].lower() == 'cheese':
                extra.append("Cheese pizza is the cheapest pizza. Simple and classic. Best for kids. Vegetarian option. No meat.")
            if row['flavor_or_name'].lower() == 'hawaiian':
                extra.append("Hawaiian pizza contains ham and pineapple. Not vegetarian. Sweet and savory. Contains pork. Tropical flavor.")
            extra.append("Available sizes: small, medium, large. You can order any pizza in small, medium, or large size. Choose your size: small, medium, or large.")
            extra.append("Small pizza is the cheapest. Large pizza is the biggest. Medium is the standard size.")
            text = (
                f"{row['flavor_or_name']} pizza. Sizes: {row['sizes']}. "
                f"{row['description']} "
                f"Prices: small: ${row['price_small']}, medium: ${row['price_medium']}, large: ${row['price_large']}. "
                + " ".join(extra)
            )
            meta = {
                "category": "pizza",
                "flavor": row['flavor_or_name'],
                "sizes": row['sizes'],
                "price_small": row['price_small'],
                "price_medium": row['price_medium'],
                "price_large": row['price_large'],
                "vegetarian": row.get('vegetarian', '')
            }
        else:
            drink_synonyms = {
                "soda": ["soda", "soft drink", "pop", "cola", "refreshing soda", "carbonated drink", "cold drink"],
                "water": ["water", "bottled water", "still water", "plain water", "refreshing water"],
                "wine": ["wine", "glass of wine", "red wine", "white wine", "alcoholic drink", "wine by the glass"]
            }
            synonyms = drink_synonyms.get(row['flavor_or_name'].lower(), [row['flavor_or_name']])
            text = (
                f"{row['flavor_or_name']} ({row['category']}): {row['description']}. Price: ${row['price']}. "
                f"We offer drinks: soda, water, wine. "
                f"{' '.join(synonyms)}. You can order {row['flavor_or_name']} with your pizza. Drinks menu includes soda, water, wine. "
                f"Order a {row['flavor_or_name']} to go with your meal."
            )
            meta = {
                "category": row['category'],
                "name": row['flavor_or_name'],
                "price": row['price']
            }
        docs.append(Document(page_content=text, metadata=meta))
    # Indexar en ChromaDB
    vectorstore = Chroma.from_documents(
        docs,
        embedding=OpenAIEmbeddings(),
        persist_directory=CHROMA_PATH
    )
    vectorstore.persist()
    current_app.logger.info("[RAG] Indexación completada, persistiendo vector store")
    return jsonify({'message': 'Menu ingested successfully', 'count': len(docs)})

@rag_bp.route('/api/menu/ask', methods=['POST'])
def ask_menu():
    data = request.get_json() or {}
    query_text = data.get('query', '')
    if not query_text:
        return jsonify({'error': 'No query provided'}), 400
    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=OpenAIEmbeddings()
    )
    docs = vectorstore.similarity_search(query_text, k=5)
    # Simular una respuesta de answer (puedes reemplazar por tu LLM o lógica de generación)
    answer = f"Top result: {docs[0].page_content}" if docs else "No relevant documents found."
    return jsonify({
        'answer': answer,
        'docs': [r.page_content for r in docs],
        'metadata': [r.metadata for r in docs]
    }) 