import os
import logging
from flask import Flask, render_template, request, jsonify, session
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_cohere import CohereEmbeddings
from langchain.chat_models import init_chat_model
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import tempfile
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback-secret-key")

# Configuration
UPLOAD_FOLDER = tempfile.mkdtemp()
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_pdf(file_path):
    """Process PDF file and create vector database"""
    try:
        # Read PDF
        with open(file_path, 'rb') as file:
            pdf_reader = PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
        
        if not text.strip():
            raise ValueError("No text could be extracted from the PDF")
        
        # Split text
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.create_documents([text])
        
        # Get API key
        cohere_api_key = os.environ.get("COHERE_API_KEY")
        if not cohere_api_key:
            raise ValueError("COHERE_API_KEY not found in environment variables")
        
        # Create embeddings and vector store
        embeddings = CohereEmbeddings(
            model="embed-english-v3.0",
            cohere_api_key=cohere_api_key
        )
        vectordb = Chroma.from_documents(docs, embeddings)
        
        return vectordb, len(docs)
    
    except Exception as e:
        logging.error(f"Error processing PDF: {str(e)}")
        raise

@app.route('/')
def index():
    """Main page"""
    # Initialize session messages if not exists
    if 'messages' not in session:
        session['messages'] = []
    
    # Check if API key is available
    cohere_api_key = os.environ.get("COHERE_API_KEY")
    
    return render_template('index.html', 
                         has_api_key=bool(cohere_api_key),
                         messages=session.get('messages', []))

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Process PDF
            vectordb, chunk_count = process_pdf(file_path)
            
            # Store vector database in session (in production, use a proper database)
            session['pdf_processed'] = True
            session['pdf_filename'] = filename
            session['chunk_count'] = chunk_count
            
            # Store vectordb reference (in production, use proper persistence)
            app.vectordb = vectordb
            
            # Clean up uploaded file
            os.remove(file_path)
            
            return jsonify({
                'success': True, 
                'message': f'PDF processed successfully! Created {chunk_count} text chunks.',
                'filename': filename
            })
        
        else:
            return jsonify({'error': 'Invalid file type. Please upload a PDF file.'}), 400
    
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle question asking"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Please enter a question'}), 400
        
        if not session.get('pdf_processed'):
            return jsonify({'error': 'Please upload a PDF file first'}), 400
        
        if not hasattr(app, 'vectordb'):
            return jsonify({'error': 'PDF processing session expired. Please upload the file again.'}), 400
        
        # Get API key
        cohere_api_key = os.environ.get("COHERE_API_KEY")
        if not cohere_api_key:
            return jsonify({'error': 'COHERE API key not configured'}), 500
        
        # Create QA chain
        retriever = app.vectordb.as_retriever()
        llm = init_chat_model("command-r-plus", model_provider="cohere", api_key=cohere_api_key)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False,
        )
        
        # Get answer
        response = qa_chain.invoke({"query": question})["result"]
        
        # Update session messages
        if 'messages' not in session:
            session['messages'] = []
        
        session['messages'].append({"role": "user", "content": question})
        session['messages'].append({"role": "assistant", "content": response})
        
        # Keep only last 20 messages to prevent session from growing too large
        if len(session['messages']) > 20:
            session['messages'] = session['messages'][-20:]
        
        session.modified = True
        
        return jsonify({
            'success': True,
            'answer': response,
            'question': question
        })
    
    except Exception as e:
        logging.error(f"Question answering error: {str(e)}")
        return jsonify({'error': f'Error getting answer: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_chat():
    """Clear chat history"""
    session['messages'] = []
    session.modified = True
    return jsonify({'success': True})

@app.route('/reset', methods=['POST'])
def reset_session():
    """Reset entire session"""
    session.clear()
    if hasattr(app, 'vectordb'):
        delattr(app, 'vectordb')
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
