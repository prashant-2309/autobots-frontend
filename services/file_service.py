import os
import zipfile
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename

class FileService:
    def __init__(self):
        # Use /tmp for Cloud Run
        self.temp_dir = '/tmp/temp'
        os.makedirs(self.temp_dir, exist_ok=True)
        
        if filename.endswith('.zip'):
            return self._process_zip_file(file)
        else:
            # Single file upload
            content = file.read().decode('utf-8')
            return content, [{'name': filename, 'content': content}]
    
    def process_multiple_uploads(self, files):
        """Process multiple uploaded files - ADDED THIS METHOD"""
        code_content = ""
        file_info = []
        
        for file in files:
            if file.filename == '':
                continue
                
            filename = secure_filename(file.filename)
            print(f"Processing file: {filename}")
            
            try:
                if filename.endswith('.zip'):
                    # Process zip file
                    zip_content, zip_files = self._process_zip_file(file)
                    code_content += zip_content
                    file_info.extend(zip_files)
                elif self._is_code_file(filename):
                    # Process individual code file
                    content = file.read().decode('utf-8')
                    code_content += f"\n\n// File: {filename}\n{content}"
                    file_info.append({
                        'name': filename,
                        'content': content
                    })
                else:
                    print(f"Skipping non-code file: {filename}")
                    
            except UnicodeDecodeError:
                print(f"Warning: Could not decode {filename} (binary file?)")
                continue
            except Exception as e:
                print(f"Warning: Error processing {filename}: {e}")
                continue
        
        return code_content, file_info
    
    def _process_zip_file(self, zip_file):
        """Process uploaded zip file"""
        code_content = ""
        file_info = []
        
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            for file_path in zip_ref.namelist():
                if self._is_code_file(file_path) and not file_path.endswith('/'):
                    try:
                        with zip_ref.open(file_path) as f:
                            content = f.read().decode('utf-8')
                            code_content += f"\n\n// File: {file_path}\n{content}"
                            file_info.append({
                                'name': os.path.basename(file_path),
                                'path': file_path,
                                'content': content
                            })
                    except UnicodeDecodeError:
                        # Skip binary files
                        print(f"Skipping binary file: {file_path}")
                        continue
                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
                        continue
        
        return code_content, file_info
    
    def create_test_zip(self, test_files):
        """Create downloadable zip file with test cases"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"test_cases_{timestamp}.zip"
        zip_path = os.path.join('/tmp/temp', zip_filename)  # Updated path
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for test_file in test_files:
                zip_file.writestr(test_file['filename'], test_file['content'])
    
    def _is_code_file(self, filename):
        """Check if file is a code file"""
        code_extensions = ['.py', '.java', '.js', '.ts', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.kt', '.swift']
        return any(filename.lower().endswith(ext) for ext in code_extensions)