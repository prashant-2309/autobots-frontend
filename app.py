from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import zipfile
from datetime import datetime
from services.git_service import GitService
from services.ai_service import AIService
from services.file_service import FileService
from services.document_service import DocumentService
from dotenv import load_dotenv
import logging
from google.cloud import logging as cloud_logging

# Load environment variables
load_dotenv()

# Initialize Cloud Logging (for production)
if os.getenv('GOOGLE_CLOUD_PROJECT'):
    try:
        client = cloud_logging.Client()
        client.setup_logging()
        print("Cloud Logging initialized")
    except Exception as e:
        print(f"Could not initialize Cloud Logging: {e}")

app = Flask(__name__)

# Cloud Run specific configuration
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'  # Use /tmp for Cloud Run
app.config['TEMP_FOLDER'] = '/tmp/temp'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Create directories in /tmp for Cloud Run
os.makedirs('/tmp/uploads', exist_ok=True)
os.makedirs('/tmp/temp', exist_ok=True)
os.makedirs('/tmp/logs', exist_ok=True)

# Initialize services
git_service = GitService()
ai_service = AIService()
file_service = FileService()
document_service = DocumentService()

# Store analysis data for test generation
analysis_cache = {}

@app.route('/')
def index():
    """Manual mode page"""
    return render_template('manual.html')

@app.route('/automatic')
def automatic():
    """Automatic mode page"""
    return render_template('automatic.html')

@app.route('/health')
def health():
    """Health check endpoint for Cloud Run"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# ... rest of the existing routes remain the same ...

@app.route('/analyze', methods=['POST'])
def analyze_code():
    try:
        data = request.get_json()
        git_url = data.get('git_url', '').strip()
        access_token = data.get('access_token', '').strip()
        manual_code = data.get('manual_code', '').strip()
        
        code_content = ""
        file_info = []
        
        logging.info(f"Analyze request - Git URL: {git_url}, Manual code length: {len(manual_code)}")
        
        # Handle Git URL
        if git_url:
            logging.info("Fetching from Git repository...")
            code_content, file_info = git_service.fetch_repository(git_url, access_token)
            logging.info(f"Fetched {len(file_info)} files from repository")
        
        # Handle manual code input
        elif manual_code:
            logging.info("Processing manual code input...")
            code_content = manual_code
            extension = '.java' if 'public class' in manual_code else '.py'
            file_info = [{'name': f'manual_input{extension}', 'content': manual_code}]
        
        if not code_content:
            return jsonify({'error': 'No code provided for analysis'}), 400
        
        logging.info("Starting AI analysis...")
        analysis_result = ai_service.analyze_code(code_content, file_info)
        
        # Cache the analysis and files for test generation
        cache_key = str(hash(code_content))
        analysis_cache[cache_key] = {
            'code_content': code_content,
            'file_info': file_info,
            'analysis': analysis_result
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'file_count': len(file_info),
            'cache_key': cache_key
        })
        
    except Exception as e:
        logging.error(f"Analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        print(f"Processing {len(files)} uploaded files...")
        
        # Process uploaded files
        code_content, file_info = file_service.process_multiple_uploads(files)
        
        if not code_content:
            return jsonify({'error': 'No valid code files found in upload'}), 400
        
        print("Starting AI analysis of uploaded files...")
        # Analyze the uploaded code
        analysis_result = ai_service.analyze_code(code_content, file_info)
        
        # Cache for test generation
        cache_key = str(hash(code_content))
        analysis_cache[cache_key] = {
            'code_content': code_content,
            'file_info': file_info,
            'analysis': analysis_result
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'file_count': len(file_info),
            'cache_key': cache_key
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-tests', methods=['POST'])
def generate_tests():
    try:
        data = request.get_json()
        cache_key = data.get('cache_key')
        
        if not cache_key or cache_key not in analysis_cache:
            return jsonify({'error': 'No analysis data found. Please analyze code first.'}), 400
        
        cached_data = analysis_cache[cache_key]
        code_content = cached_data['code_content']
        file_info = cached_data['file_info']
        
        print(f"Generating tests for {len(file_info)} files...")
        
        # Generate test cases using Vertex AI
        test_files = ai_service.generate_test_cases(code_content, file_info)
        
        if not test_files:
            return jsonify({'error': 'No test files were generated'}), 400
        
        # Create downloadable zip file
        zip_path = file_service.create_test_zip(test_files)
        zip_filename = os.path.basename(zip_path)
        
        print(f"Generated {len(test_files)} test files, packaged in {zip_filename}")
        
        return jsonify({
            'success': True,
            'test_files': [{'filename': tf['filename'], 'size': len(tf['content'])} for tf in test_files],
            'download_url': f'/download/{zip_filename}',
            'total_files': len(test_files)
        })
        
    except Exception as e:
        print(f"Test generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join('temp', filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join('/tmp/temp', filename)  # Use /tmp for Cloud Run
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    logging.info("Starting Test Generator Application...")
    logging.info(f"Project ID: {os.getenv('GOOGLE_CLOUD_PROJECT', 'Not set')}")
    logging.info(f"Region: {os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')}")
    logging.info(f"Port: {port}")
    
    app.run(debug=False, host='0.0.0.0', port=port)