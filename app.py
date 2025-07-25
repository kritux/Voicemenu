from flask import Flask, render_template, request, jsonify
import base64
import io
import openai
import os
from config import Config
from models import db, Menu, Drink, Order
import json
from audio_provider import FileAudioProvider
import tempfile
import json
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from dotenv import load_dotenv
load_dotenv()
from rag.chroma_query import ChromaRAG
from rag.rag import rag_bp
from audio_parse import parse_order_with_ai

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe_audio', methods=['POST'])
def transcribe_audio():
    data = request.get_json()
    audio_data = data.get('audio')
    
    # Decodificar el audio base64 con manejo de errores
    try:
        audio_bytes = base64.b64decode(audio_data.split(',')[1])
    except Exception as e:
        return jsonify({'error': f"Error decoding audio: {str(e)}"}), 400
    
    # Crear un archivo temporal para OpenAI
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.webm"
    
    try:
        # Usar Whisper con configuración optimizada para acentos
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en",
            response_format="text",
            temperature=0.2,  # Más flexible para acentos
            prompt="This is a restaurant order. Common words: pizza, pepperoni, cheese, hawaiian, vegetarian, small, medium, large, water, soda, tea, wine."
        )
        
        # Post-procesamiento con GPT-4o para corregir y mejorar
        try:
            corrected_text = post_process_transcription(transcript)
            return jsonify({'text': corrected_text})
        except Exception as e:
            print(f"Post-processing error: {e}")
            # Si falla el post-procesamiento, devolver transcripción original
            return jsonify({'text': transcript})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/upload', methods=['POST'])
def audio_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    allowed_exts = ('.mp3', '.mp4')
    allowed_mimes = ('audio/mpeg', 'audio/mp3', 'audio/mp4', 'video/mp4')
    if not (file.filename.lower().endswith(allowed_exts) or file.mimetype in allowed_mimes):
        return jsonify({'error': 'Only MP3 or MP4 files are supported.'}), 400
    
    # Guardar archivo temporalmente
    import tempfile
    import os
    ext = '.mp3' if file.filename.lower().endswith('.mp3') else '.mp4'
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        file.save(tmp.name)
        audio_path = tmp.name
    app.logger.info(f"Received audio file: {audio_path}")
    
    # Obtener bytes del archivo
    from audio_provider import FileAudioProvider
    try:
        audio_bytes = FileAudioProvider().get_audio_bytes(audio_path)
    except Exception as e:
        app.logger.error(f"Error reading audio: {e}")
        os.remove(audio_path)
        return jsonify({'error': str(e)}), 500
    
    # Transcribir con Whisper (OpenAI)
    try:
        import io
        import openai
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = file.filename
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"
        )
        transcript_text = transcript.text if hasattr(transcript, 'text') else transcript
        app.logger.info(f"Whisper input bytes={len(audio_bytes)}, output='{transcript_text}'")
    except Exception as e:
        app.logger.error(f"Whisper transcription error: {e}")
        os.remove(audio_path)
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    
    return jsonify({"transcript": transcript_text})

@app.route("/audio/parse", methods=["POST"])
def audio_parse():
    transcript = request.form["transcript"]
    order = parse_order_with_ai(transcript)
    return render_template("order_confirm.html", order=order)

@app.route("/audio/confirm", methods=["POST"])
def confirm_order():
    order = request.form["order_json"]
    action = request.form["action"]

    if action == "edit":
        return redirect(url_for("audio_demo"))

    # aquí sí guardas en tu base de datos y luego vas a kitchen.html
    # por ejemplo:
    # from models import Order, db
    # data = json.loads(order)
    # new_order = Order(items=data["items"])
    # db.session.add(new_order)
    # db.session.commit()

    return render_template("kitchen.html", order=json.loads(order))

def post_process_transcription(text):
    """Post-procesar transcripción con GPT-4o para corregir errores y acentos"""
    
    # Verificar que el texto sea válido
    if not text or not isinstance(text, str):
        print(f"Invalid text received: {text}")
        return text if text else ""
    
    # Mapeo de palabras comúnmente mal pronunciadas
    common_mispronunciations = {
        'peperoni': 'pepperoni',
        'peperonni': 'pepperoni',
        'peperony': 'pepperoni',
        'hawai': 'hawaiian',
        'hawaii': 'hawaiian',
        'vegatarian': 'vegetarian',
        'vegatarian': 'vegetarian',
        'mediam': 'medium',
        'meduim': 'medium',
        'soda': 'soda',
        'soda': 'soda',
        'wine': 'wine',
        'wine': 'wine'
    }
    
    # Aplicar correcciones básicas
    try:
        corrected_text = text.lower()
        for wrong, correct in common_mispronunciations.items():
            corrected_text = corrected_text.replace(wrong, correct)
    except Exception as e:
        print(f"Error in basic corrections: {e}")
        corrected_text = text
    
    # Usar GPT-4o para corrección avanzada REVISAR
    try:
        prompt = f"""
        Correct this restaurant order transcription, fixing any pronunciation errors, accents, or unclear words.
        Focus on food items: pizza types (cheese, pepperoni, hawaiian, vegetarian), sizes (small, medium, large), and drinks (water, soda, tea, wine).
        
        Original: "{corrected_text}"
        Corrected: 
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that corrects restaurant order transcriptions. Return only the corrected text, nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        gpt_corrected = response.choices[0].message.content
        return gpt_corrected.strip() if gpt_corrected else corrected_text
        
    except Exception as e:
        print(f"GPT correction failed: {e}")
        return corrected_text

def extract_order_manually(text):
    """Extraer información de la orden manualmente si GPT no devuelve JSON válido"""
    text_lower = text.lower()
    
    # Buscar pizza
    pizza_types = ['cheese', 'pepperoni', 'hawaiian', 'vegetarian']
    pizza = None
    for p in pizza_types:
        if p in text_lower:
            pizza = p
            break
    
    # Buscar tamaño
    size_types = ['small', 'medium', 'large']
    size = None
    for s in size_types:
        if s in text_lower:
            size = s
            break
    
    # Buscar bebida
    drink_types = ['water', 'soda', 'tea', 'wine']
    drink = None
    for d in drink_types:
        if d in text_lower:
            drink = d
            break
    
    return {
        'pizza': pizza,
        'size': size,
        'drink': drink
    }

@app.route('/kitchen')
def kitchen():
    return render_template('kitchen.html')

@app.route('/api/orders')
def get_orders():
    try:
        orders = Order.query.filter(Order.status != 'completed').order_by(Order.created_at.desc()).all()
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'pizza': order.pizza,
                'size': order.size,
                'drink': order.drink,
                'total': order.total,
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'order_details': order.order_details
            })
        return jsonify({'orders': orders_data})
    except Exception as e:
        print(f"Database error: {e}")
        # Retornar lista vacía si hay error de base de datos
        return jsonify({'orders': []})

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')
    
    order = Order.query.get(order_id)
    if order:
        order.status = new_status
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Order not found'}), 404

@app.route('/process_order', methods=['POST'])
def process_order():
    data = request.get_json()
    text = data.get('text', '').lower()
    
    # Prompt simplificado para extraer keywords
    prompt = f"""
    Extract ONLY these keywords from the order: pizza_type, size, drink.
    
    Return ONLY this JSON format:
    {{"pizza": "keyword", "size": "keyword", "drink": "keyword"}}
    
    Keywords to find:
    - Pizza: cheese, pepperoni, hawaiian, vegetarian
    - Size: small, medium, large  
    - Drink: water, soda, tea, wine
    
    Order: "{text}"
    
    If not found, use null. Return ONLY the JSON.
    """
    
    try:
        # Usar GPT-4o para extraer keywords
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a keyword extractor. Return ONLY valid JSON with pizza, size, and drink keywords."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=50
        )
        
        # Parsear la respuesta de GPT
        gpt_response = response.choices[0].message.content
        if gpt_response:
            try:
                order_details = json.loads(gpt_response)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"GPT response: {gpt_response}")
                # Intentar extraer información manualmente si falla JSON
                order_details = extract_order_manually(gpt_response)
        else:
            return jsonify({'message': "Error: No response from GPT"})
        
        pizza = order_details.get('pizza')
        size = order_details.get('size')
        drink = order_details.get('drink')
        
        # Calcular precios
        size_prices = {'small': 2.0, 'medium': 3.0, 'large': 5.0}
        items = []
        total = 0
        order_details_json = {}
        
        if pizza and size:
            pizza_price = size_prices.get(size, 0)
            items.append(f"Pizza: {pizza.capitalize()} ({size.capitalize()}) (${pizza_price:.2f})")
            total += pizza_price
            order_details_json['pizza_price'] = pizza_price
        
        if drink:
            drink_obj = Drink.query.filter_by(name=drink.capitalize()).first()
            if drink_obj:
                items.append(f"Drink: {drink_obj.name} (${drink_obj.price:.2f})")
                total += drink_obj.price
                order_details_json['drink_price'] = drink_obj.price
        
        if not items:
            message = "Sorry, I couldn't understand your order. Please try again."
            return jsonify({'message': message})
        
        # Guardar orden en la base de datos
        new_order = Order(
            pizza=pizza.capitalize() if pizza else '',
            size=size.capitalize() if size else '',
            drink=drink.capitalize() if drink else '',
            total=total,
            status='pending',
            order_details=json.dumps(order_details_json)
        )
        db.session.add(new_order)
        db.session.commit()
        
        message = "Order summary:\n" + "\n".join(items) + f"\nTotal: ${total:.2f}\nOrder #: {new_order.id}"
        return jsonify({'message': message})
        
    except Exception as e:
        return jsonify({'message': f"Error processing order: {str(e)}"})

@app.route('/audio/demo')
def audio_demo():
    return render_template('audio_demo.html')

@app.route('/rag/query', methods=['POST'])
def rag_query():
    data = request.get_json()
    query_text = data.get('query', '')
    app.logger.info(f"RAG query input: '{query_text}'")
    try:
        rag = ChromaRAG()
        results = rag.query(query_text, n_results=3)
        app.logger.info(f"RAG query output: {results}")
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"RAG query error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/rag/demo')
def rag_demo():
    return render_template('rag_query_demo.html')

app.register_blueprint(rag_bp)

if __name__ == '__main__':
    app.run(debug=True) 