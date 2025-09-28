import os
import tempfile
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle
import re

class DiagramService:
    def __init__(self):
        self.temp_dir = '/tmp/temp'  # Use /tmp for Cloud Run
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def generate_code_diagram(self, code_content, filename):
        """Generate UML-style code structure diagram"""
        try:
            if filename.endswith('.java'):
                return self._generate_java_uml_diagram(code_content, filename)
            elif filename.endswith('.py'):
                return self._generate_python_uml_diagram(code_content, filename)
            else:
                return self._generate_generic_uml_diagram(code_content, filename)
        except Exception as e:
            print(f"Error generating diagram for {filename}: {e}")
            return None
    
    def _generate_java_uml_diagram(self, code_content, filename):
        """Generate UML-style diagram for Java code"""
        structure = self._parse_java_structure(code_content)
        
        # Calculate diagram size based on content
        methods = structure.get('methods', [])
        fields = structure.get('fields', [])
        class_name = structure.get('class_name', 'Unknown')
        
        # Set up the plot
        fig, ax = plt.subplots(1, 1, figsize=(10, 8))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # Title
        ax.text(5, 9.5, f"Java Class Structure: {filename}", 
                ha='center', va='center', fontsize=16, fontweight='bold', color='#2c3e50')
        
        # Calculate class box height based on content
        content_lines = len(fields) + len(methods) + 1  # +1 for class name
        box_height = max(3, min(6, content_lines * 0.3 + 1))
        box_top = 8
        
        # Main class box
        class_box = FancyBboxPatch((2, box_top - box_height), 6, box_height,
                                   boxstyle="round,pad=0.05",
                                   facecolor='#e8f4fd', 
                                   edgecolor='#3498db',
                                   linewidth=2)
        ax.add_patch(class_box)
        
        # Class name section (header)
        header_box = Rectangle((2, box_top - 0.6), 6, 0.6,
                              facecolor='#3498db', 
                              edgecolor='#3498db')
        ax.add_patch(header_box)
        
        # Class name
        ax.text(5, box_top - 0.3, class_name, 
                ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        
        # Current y position for content
        current_y = box_top - 0.8
        
        # Fields section
        if fields:
            # Fields separator line
            ax.plot([2.2, 7.8], [current_y, current_y], color='#3498db', linewidth=1)
            current_y -= 0.2
            
            for field in fields[:5]:  # Limit to 5 fields
                ax.text(2.3, current_y, f"- {field}", 
                       ha='left', va='center', fontsize=10, color='#2c3e50')
                current_y -= 0.25
            
            if len(fields) > 5:
                ax.text(2.3, current_y, f"... and {len(fields)-5} more fields", 
                       ha='left', va='center', fontsize=9, style='italic', color='#7f8c8d')
                current_y -= 0.3
        
        # Methods separator line
        if fields:
            ax.plot([2.2, 7.8], [current_y, current_y], color='#3498db', linewidth=1)
            current_y -= 0.2
        
        # Methods section
        for method in methods[:8]:  # Limit to 8 methods
            ax.text(2.3, current_y, f"+ {method}", 
                   ha='left', va='center', fontsize=10, color='#2c3e50')
            current_y -= 0.25
        
        if len(methods) > 8:
            ax.text(2.3, current_y, f"... and {len(methods)-8} more methods", 
                   ha='left', va='center', fontsize=9, style='italic', color='#7f8c8d')
        
        # Statistics box
        stats_y = box_top - box_height - 1.5
        stats_box = FancyBboxPatch((2, stats_y - 0.8), 2.5, 0.8,
                                   boxstyle="round,pad=0.05",
                                   facecolor='#f8f9fa', 
                                   edgecolor='#6c757d',
                                   linewidth=1)
        ax.add_patch(stats_box)
        
        lines_count = len(code_content.split('\n'))
        ax.text(3.25, stats_y - 0.2, f"Methods: {len(methods)}", 
               ha='center', va='center', fontsize=10, fontweight='bold')
        ax.text(3.25, stats_y - 0.6, f"Lines: {lines_count}", 
               ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Save diagram
        plt.tight_layout()
        diagram_path = os.path.join(self.temp_dir, f"uml_diagram_{filename}_{hash(code_content)}.png")
        plt.savefig(diagram_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return diagram_path
    
    def _generate_python_uml_diagram(self, code_content, filename):
        """Generate UML-style diagram for Python code"""
        structure = self._parse_python_structure(code_content)
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 10)
        ax.axis('off')
        
        # Title
        ax.text(6, 9.5, f"Python Module Structure: {filename}", 
                ha='center', va='center', fontsize=16, fontweight='bold', color='#2c3e50')
        
        functions = structure.get('functions', [])
        classes = structure.get('classes', [])
        
        current_x = 1
        
        # Draw classes
        for i, class_name in enumerate(classes[:3]):  # Max 3 classes
            class_methods = self._get_class_methods(code_content, class_name)
            
            # Calculate box height
            box_height = max(2, min(4, len(class_methods) * 0.25 + 1))
            box_top = 7.5
            
            # Class box
            class_box = FancyBboxPatch((current_x, box_top - box_height), 3, box_height,
                                       boxstyle="round,pad=0.05",
                                       facecolor='#e8f5e8', 
                                       edgecolor='#27ae60',
                                       linewidth=2)
            ax.add_patch(class_box)
            
            # Class header
            header_box = Rectangle((current_x, box_top - 0.5), 3, 0.5,
                                  facecolor='#27ae60', 
                                  edgecolor='#27ae60')
            ax.add_patch(header_box)
            
            # Class name
            ax.text(current_x + 1.5, box_top - 0.25, class_name, 
                   ha='center', va='center', fontsize=12, fontweight='bold', color='white')
            
            # Methods
            method_y = box_top - 0.8
            for method in class_methods[:6]:
                ax.text(current_x + 0.2, method_y, f"+ {method}", 
                       ha='left', va='center', fontsize=9, color='#2c3e50')
                method_y -= 0.2
            
            if len(class_methods) > 6:
                ax.text(current_x + 0.2, method_y, f"... +{len(class_methods)-6} more", 
                       ha='left', va='center', fontsize=8, style='italic', color='#7f8c8d')
            
            current_x += 3.5
        
        # Draw module functions box
        if functions:
            func_box_height = max(2, min(4, len(functions) * 0.2 + 0.8))
            func_box_top = 4
            
            func_box = FancyBboxPatch((1, func_box_top - func_box_height), 4, func_box_height,
                                      boxstyle="round,pad=0.05",
                                      facecolor='#fff3e0', 
                                      edgecolor='#f39c12',
                                      linewidth=2)
            ax.add_patch(func_box)
            
            # Function header
            func_header = Rectangle((1, func_box_top - 0.5), 4, 0.5,
                                   facecolor='#f39c12', 
                                   edgecolor='#f39c12')
            ax.add_patch(func_header)
            
            ax.text(3, func_box_top - 0.25, "Module Functions", 
                   ha='center', va='center', fontsize=12, fontweight='bold', color='white')
            
            # Functions
            func_y = func_box_top - 0.8
            for func in functions[:8]:
                ax.text(1.2, func_y, f"+ {func}()", 
                       ha='left', va='center', fontsize=9, color='#2c3e50')
                func_y -= 0.2
            
            if len(functions) > 8:
                ax.text(1.2, func_y, f"... +{len(functions)-8} more functions", 
                       ha='left', va='center', fontsize=8, style='italic', color='#7f8c8d')
        
        # Statistics
        stats_box = FancyBboxPatch((7, 2.5), 3, 1.5,
                                   boxstyle="round,pad=0.05",
                                   facecolor='#f8f9fa', 
                                   edgecolor='#6c757d',
                                   linewidth=1)
        ax.add_patch(stats_box)
        
        lines_count = len(code_content.split('\n'))
        ax.text(8.5, 3.6, "Statistics", ha='center', va='center', 
               fontsize=11, fontweight='bold')
        ax.text(8.5, 3.2, f"Classes: {len(classes)}", ha='center', va='center', fontsize=10)
        ax.text(8.5, 2.9, f"Functions: {len(functions)}", ha='center', va='center', fontsize=10)
        ax.text(8.5, 2.6, f"Lines: {lines_count}", ha='center', va='center', fontsize=10)
        
        plt.tight_layout()
        diagram_path = os.path.join(self.temp_dir, f"uml_diagram_{filename}_{hash(code_content)}.png")
        plt.savefig(diagram_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return diagram_path
    
    def _generate_generic_uml_diagram(self, code_content, filename):
        """Generate generic UML-style diagram"""
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        ax.set_xlim(0, 8)
        ax.set_ylim(0, 6)
        ax.axis('off')
        
        # Title
        ax.text(4, 5.5, f"Code Structure: {filename}", 
                ha='center', va='center', fontsize=14, fontweight='bold', color='#2c3e50')
        
        # Main box
        main_box = FancyBboxPatch((1, 2), 6, 2.5,
                                  boxstyle="round,pad=0.05",
                                  facecolor='#f8f9fa', 
                                  edgecolor='#6c757d',
                                  linewidth=2)
        ax.add_patch(main_box)
        
        # Header
        header_box = Rectangle((1, 4), 6, 0.5,
                              facecolor='#6c757d', 
                              edgecolor='#6c757d')
        ax.add_patch(header_box)
        
        ax.text(4, 4.25, filename, ha='center', va='center', 
               fontsize=12, fontweight='bold', color='white')
        
        # Content analysis
        lines = code_content.split('\n')
        non_empty_lines = len([l for l in lines if l.strip()])
        
        # Estimate structure
        estimated_functions = len(re.findall(r'(function|def |func |sub |procedure)', code_content, re.IGNORECASE))
        estimated_classes = len(re.findall(r'(class |struct |interface)', code_content, re.IGNORECASE))
        
        content_y = 3.5
        ax.text(4, content_y, f"Total Lines: {len(lines)}", ha='center', va='center', fontsize=10)
        content_y -= 0.3
        ax.text(4, content_y, f"Code Lines: {non_empty_lines}", ha='center', va='center', fontsize=10)
        content_y -= 0.3
        ax.text(4, content_y, f"Functions: ~{estimated_functions}", ha='center', va='center', fontsize=10)
        content_y -= 0.3
        ax.text(4, content_y, f"Classes: ~{estimated_classes}", ha='center', va='center', fontsize=10)
        
        plt.tight_layout()
        diagram_path = os.path.join(self.temp_dir, f"uml_diagram_{filename}_{hash(code_content)}.png")
        plt.savefig(diagram_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return diagram_path
    
    def _parse_java_structure(self, code_content):
        """Parse Java code to extract detailed structure"""
        structure = {
            'class_name': 'Unknown',
            'methods': [],
            'fields': [],
            'constructors': []
        }
        
        # Extract class name
        class_match = re.search(r'public\s+class\s+(\w+)', code_content)
        if class_match:
            structure['class_name'] = class_match.group(1)
        
        # Extract fields
        field_pattern = r'(?:private|public|protected)\s+(?:static\s+)?(?:final\s+)?\w+(?:<[^>]+>)?\s+(\w+)\s*[;=]'
        fields = re.findall(field_pattern, code_content)
        structure['fields'] = list(set(fields))
        
        # Extract methods (excluding constructors)
        method_pattern = r'(?:public|private|protected)\s+(?:static\s+)?(?:\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*\{'
        methods = re.findall(method_pattern, code_content)
        class_name = structure['class_name']
        structure['methods'] = [m for m in set(methods) if m != class_name]
        
        # Extract constructors
        constructor_pattern = rf'(?:public|private|protected)\s+{class_name}\s*\([^)]*\)\s*\{{'
        constructors = re.findall(constructor_pattern, code_content)
        structure['constructors'] = constructors
        
        return structure
    
    def _parse_python_structure(self, code_content):
        """Parse Python code to extract detailed structure"""
        structure = {
            'functions': [],
            'classes': [],
            'imports': []
        }
        
        lines = code_content.split('\n')
        current_class = None
        
        for line in lines:
            stripped_line = line.strip()
            
            # Extract top-level functions
            if stripped_line.startswith('def ') and '(' in stripped_line and line.startswith('def '):
                func_name = stripped_line.split('def ')[1].split('(')[0].strip()
                structure['functions'].append(func_name)
            
            # Extract classes
            elif stripped_line.startswith('class ') and ':' in stripped_line:
                class_name = stripped_line.split('class ')[1].split(':')[0].split('(')[0].strip()
                structure['classes'].append(class_name)
                current_class = class_name
            
            # Extract imports
            elif stripped_line.startswith(('import ', 'from ')):
                structure['imports'].append(stripped_line)
        
        return structure
    
    def _get_class_methods(self, code_content, class_name):
        """Extract methods for a specific Python class"""
        methods = []
        lines = code_content.split('\n')
        in_class = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # Check if we're entering the class
            if stripped_line.startswith(f'class {class_name}'):
                in_class = True
                continue
            
            # Check if we're leaving the class (another class starts or no indentation)
            elif in_class and line and not line.startswith(' ') and not line.startswith('\t'):
                if stripped_line.startswith('class '):
                    in_class = False
                    continue
            
            # Extract method from within the class
            if in_class and stripped_line.startswith('def ') and '(' in stripped_line:
                method_name = stripped_line.split('def ')[1].split('(')[0].strip()
                if method_name not in ['__init__', '__str__', '__repr__']:  # Skip special methods
                    methods.append(method_name)
        
        return methods