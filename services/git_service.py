import requests
import base64
import os
import time
import json
from urllib.parse import urlparse
import urllib3

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GitService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TestGenerator-App/1.0 (Code Analysis Tool)',
            'Accept': 'application/vnd.github.v3+json',
            'Accept-Encoding': 'gzip, deflate'
        })
        # Keep SSL verification on but handle errors gracefully
        self.session.verify = True
        
        # Rate limiting tracking
        self.last_request_time = 0
        self.requests_count = 0
        self.rate_limit_reset = 0

    def fetch_repository(self, git_url, access_token=None):
        """Fetch repository content from Git URL"""
        try:
            if 'github.com' in git_url:
                return self._fetch_github_repo(git_url, access_token)
            elif 'gitlab.com' in git_url:
                return self._fetch_gitlab_repo(git_url, access_token)
            else:
                raise ValueError("Unsupported Git provider. Only GitHub and GitLab are supported.")
                
        except Exception as e:
            print(f"Error fetching repository: {e}")
            raise Exception(f"Failed to fetch repository: {str(e)}")

    def _rate_limit_check(self):
        """Check and handle rate limiting"""
        current_time = time.time()
        
        # Wait at least 1 second between requests
        if current_time - self.last_request_time < 1:
            time.sleep(1 - (current_time - self.last_request_time))
        
        self.last_request_time = time.time()
        self.requests_count += 1

    def _fetch_github_repo(self, git_url, access_token=None):
        """Fetch GitHub repository content with multiple fallback methods"""
        # Parse GitHub URL
        parsed = urlparse(git_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub URL format")
        
        owner = path_parts[0]
        repo = path_parts[1]
        
        # Remove .git suffix if present
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        print(f"Fetching GitHub repo: {owner}/{repo}")
        
        # Setup headers
        headers = dict(self.session.headers)
        if access_token:
            headers['Authorization'] = f'token {access_token}'
            print("Using provided access token for authentication")
        
        # Try multiple methods
        methods = [
            ('GitHub API', lambda: self._fetch_via_github_api(owner, repo, headers)),
            ('Raw GitHub', lambda: self._fetch_via_raw_github(owner, repo, headers)),
            ('Archive Download', lambda: self._fetch_via_github_archive(owner, repo, headers))
        ]
        
        for method_name, method_func in methods:
            try:
                print(f"Trying {method_name}...")
                code_content, file_info = method_func()
                if file_info:
                    print(f"✅ Success with {method_name}: Found {len(file_info)} files")
                    return code_content, file_info
                else:
                    print(f"❌ {method_name} returned no files")
            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
                continue
        
        raise Exception("All GitHub access methods failed. Repository might be private or rate limit exceeded.")

    def _fetch_via_github_api(self, owner, repo, headers):
        """Method 1: Use GitHub API"""
        self._rate_limit_check()
        
        # Check repository accessibility first
        repo_url = f'https://api.github.com/repos/{owner}/{repo}'
        repo_response = self.session.get(repo_url, headers=headers, timeout=30)
        
        if repo_response.status_code == 404:
            raise Exception("Repository not found or not accessible")
        elif repo_response.status_code == 403:
            rate_limit_remaining = repo_response.headers.get('X-RateLimit-Remaining', '0')
            if rate_limit_remaining == '0':
                reset_time = repo_response.headers.get('X-RateLimit-Reset', '0')
                raise Exception(f"GitHub API rate limit exceeded. Resets at {reset_time}")
            else:
                raise Exception("Access forbidden. Repository might be private.")
        elif repo_response.status_code != 200:
            raise Exception(f"GitHub API error: {repo_response.status_code}")
        
        # Get repository tree recursively
        tree_url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1'
        
        # Try 'main' branch first, then 'master'
        for branch in ['main', 'master']:
            self._rate_limit_check()
            tree_url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1'
            tree_response = self.session.get(tree_url, headers=headers, timeout=30)
            
            if tree_response.status_code == 200:
                break
        else:
            raise Exception("Could not access repository tree (tried main and master branches)")
        
        tree_data = tree_response.json()
        
        # Filter for code files
        code_files = []
        for item in tree_data.get('tree', []):
            if item['type'] == 'blob' and self._is_code_file(item['path']):
                code_files.append(item)
        
        print(f"Found {len(code_files)} code files via API")
        
        # Download file contents
        return self._download_github_files_api(code_files, owner, repo, headers)

    def _fetch_via_raw_github(self, owner, repo, headers):
        """Method 2: Use raw.githubusercontent.com"""
        print("Attempting raw GitHub access...")
        
        # First, get the file list using API (lightweight call)
        files_to_download = []
        
        # Common code file patterns
        common_paths = [
            'src/main/java',
            'src/test/java',
            'src',
            'main',
            'lib',
            'app',
            'server',
            'client'
        ]
        
        # Try to get repository structure via API first
        try:
            for branch in ['main', 'master']:
                tree_url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1'
                response = self.session.get(tree_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    tree_data = response.json()
                    for item in tree_data.get('tree', []):
                        if item['type'] == 'blob' and self._is_code_file(item['path']):
                            files_to_download.append({
                                'path': item['path'],
                                'name': os.path.basename(item['path']),
                                'branch': branch
                            })
                    break
        except:
            pass
        
        if not files_to_download:
            raise Exception("Could not find files via raw GitHub method")
        
        # Download files using raw.githubusercontent.com
        return self._download_raw_github_files(files_to_download, owner, repo, headers)

    def _fetch_via_github_archive(self, owner, repo, headers):
        """Method 3: Download repository as ZIP archive"""
        import zipfile
        import io
        
        for branch in ['main', 'master']:
            archive_url = f'https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip'
            
            try:
                response = self.session.get(archive_url, headers=headers, timeout=60)
                
                if response.status_code == 200:
                    # Extract ZIP content
                    zip_content = io.BytesIO(response.content)
                    
                    code_content = ""
                    file_info = []
                    
                    with zipfile.ZipFile(zip_content, 'r') as zip_file:
                        for file_path in zip_file.namelist():
                            if self._is_code_file(file_path) and not file_path.endswith('/'):
                                try:
                                    with zip_file.open(file_path) as f:
                                        content = f.read().decode('utf-8')
                                        # Remove the repository prefix from path
                                        clean_path = '/'.join(file_path.split('/')[1:])
                                        
                                        code_content += f"\n\n// File: {clean_path}\n{content}"
                                        file_info.append({
                                            'name': os.path.basename(clean_path),
                                            'path': clean_path,
                                            'content': content
                                        })
                                except UnicodeDecodeError:
                                    continue
                    
                    if file_info:
                        return code_content, file_info
                    
            except Exception as e:
                print(f"Archive download failed for branch {branch}: {e}")
                continue
        
        raise Exception("Archive download method failed")

    def _download_github_files_api(self, files, owner, repo, headers):
        """Download files using GitHub API"""
        code_content = ""
        file_info = []
        
        for i, file_data in enumerate(files[:20]):  # Limit to 20 files to avoid rate limits
            try:
                print(f"Downloading {i+1}/{min(len(files), 20)}: {file_data['path']}")
                
                self._rate_limit_check()
                
                # Get file content via API
                file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_data['path']}"
                file_response = self.session.get(file_url, headers=headers, timeout=30)
                
                if file_response.status_code == 200:
                    file_json = file_response.json()
                    
                    if file_json.get('encoding') == 'base64':
                        content = base64.b64decode(file_json['content']).decode('utf-8')
                    else:
                        content = file_json.get('content', '')
                    
                    code_content += f"\n\n// File: {file_data['path']}\n{content}"
                    file_info.append({
                        'name': os.path.basename(file_data['path']),
                        'path': file_data['path'],
                        'content': content
                    })
                else:
                    print(f"Warning: Could not download {file_data['path']}: HTTP {file_response.status_code}")
                    
            except Exception as e:
                print(f"Warning: Error downloading {file_data['path']}: {e}")
                continue
        
        return code_content, file_info

    def _download_raw_github_files(self, files, owner, repo, headers):
        """Download files using raw.githubusercontent.com"""
        code_content = ""
        file_info = []
        
        for i, file_data in enumerate(files[:20]):  # Limit to avoid timeouts
            try:
                print(f"Downloading raw {i+1}/{min(len(files), 20)}: {file_data['path']}")
                
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{file_data['branch']}/{file_data['path']}"
                
                # Use different headers for raw downloads
                raw_headers = {
                    'User-Agent': headers.get('User-Agent', 'TestGenerator-App/1.0')
                }
                
                response = self.session.get(raw_url, headers=raw_headers, timeout=30)
                
                if response.status_code == 200:
                    content = response.text
                    code_content += f"\n\n// File: {file_data['path']}\n{content}"
                    file_info.append({
                        'name': file_data['name'],
                        'path': file_data['path'],
                        'content': content
                    })
                else:
                    print(f"Warning: Could not download {file_data['path']}: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"Warning: Error downloading {file_data['path']}: {e}")
                continue
        
        return code_content, file_info

    def _fetch_gitlab_repo(self, git_url, access_token=None):
        """Fetch GitLab repository content"""
        parsed = urlparse(git_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError("Invalid GitLab URL format")
        
        owner = path_parts[0]
        repo = path_parts[1]
        
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        headers = {'User-Agent': 'TestGenerator-App/1.0'}
        if access_token:
            headers['PRIVATE-TOKEN'] = access_token
        
        # GitLab API uses project ID or encoded path
        project_path = f"{owner}%2F{repo}"
        
        try:
            # Get project info first
            project_url = f'https://gitlab.com/api/v4/projects/{project_path}'
            project_response = self.session.get(project_url, headers=headers, timeout=30)
            
            if project_response.status_code != 200:
                raise Exception(f"GitLab project not accessible: {project_response.status_code}")
            
            # Get repository tree
            tree_url = f'https://gitlab.com/api/v4/projects/{project_path}/repository/tree?recursive=true&per_page=100'
            tree_response = self.session.get(tree_url, headers=headers, timeout=30)
            
            if tree_response.status_code != 200:
                raise Exception(f"GitLab tree not accessible: {tree_response.status_code}")
            
            tree = tree_response.json()
            
            # Filter for code files
            code_files = [item for item in tree if item['type'] == 'blob' and self._is_code_file(item['name'])]
            
            print(f"Found {len(code_files)} code files in GitLab repo")
            
            # Download file contents
            return self._download_gitlab_files(code_files, project_path, headers)
            
        except Exception as e:
            raise Exception(f"GitLab fetch error: {str(e)}")

    def _download_gitlab_files(self, files, project_path, headers):
        """Download GitLab file contents"""
        code_content = ""
        file_info = []
        
        for i, file_data in enumerate(files[:20]):  # Limit to 20 files
            try:
                print(f"Downloading GitLab {i+1}/{min(len(files), 20)}: {file_data['path']}")
                
                # Encode file path for URL
                encoded_path = file_data['path'].replace('/', '%2F')
                file_url = f"https://gitlab.com/api/v4/projects/{project_path}/repository/files/{encoded_path}/raw?ref=main"
                
                file_response = self.session.get(file_url, headers=headers, timeout=30)
                
                if file_response.status_code == 200:
                    content = file_response.text
                    code_content += f"\n\n// File: {file_data['path']}\n{content}"
                    file_info.append({
                        'name': file_data['name'],
                        'path': file_data['path'],
                        'content': content
                    })
                else:
                    print(f"Warning: Could not download {file_data['path']}: HTTP {file_response.status_code}")
                    
            except Exception as e:
                print(f"Warning: Error downloading {file_data['path']}: {e}")
                continue
        
        return code_content, file_info

    def _is_code_file(self, filename):
        """Check if file is a code file we want to analyze"""
        if not filename:
            return False
            
        # Skip test files, build files, and config files
        skip_patterns = [
            'test_v','archive','spec', '.git', 'node_modules', 'target', 'build',
            '.gradle', '.maven', 'dist', 'out', '__pycache__', '.idea',
            'package-lock.json', 'yarn.lock', '.gitignore', 'README'
        ]
        
        filename_lower = filename.lower()
        for pattern in skip_patterns:
            if pattern in filename_lower:
                return False
        
        # Check for code file extensions
        code_extensions = ['.py', '.java', '.js', '.ts', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.kt', '.swift', '.scala', '.rs']
        return any(filename_lower.endswith(ext) for ext in code_extensions)