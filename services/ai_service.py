import os
import vertexai
from vertexai.generative_models import GenerativeModel
import re
from typing import Dict, List

class AIService:
    def __init__(self):
        # Initialize Vertex AI
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
        
        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel("gemini-2.5-flash-lite")
            print(f"✅ Vertex AI configured - Project: {self.project_id}, Location: {self.location}")
        except Exception as e:
            print(f"❌ Error configuring Vertex AI: {e}")
            self.model = None
    
    def analyze_code(self, code_content, file_info):
        """Comprehensive AI-based code analysis"""
        if not self.model:
            return self._fallback_analysis()
        
        try:
            prompt = f"""
            You are an expert software architect and code quality analyst. Perform a comprehensive analysis of the following codebase.

            CODEBASE OVERVIEW:
            - Total files: {len(file_info)}
            - File types: {', '.join(set([f['name'].split('.')[-1] for f in file_info if '.' in f['name']]))}
            - Files: {', '.join([f['name'] for f in file_info[:10]])}{'...' if len(file_info) > 10 else ''}

            CODE TO ANALYZE:
            {code_content[:12000]}

            PROVIDE ANALYSIS IN EXACTLY THIS FORMAT WITH CLEAR SECTIONS:

            1. **CODE QUALITY ASSESSMENT**
            - Overall quality rating and reasoning
            - Code readability assessment
            - Best practices adherence
            - Code organization evaluation

            2. **COMPLEXITY ANALYSIS**
            - Cyclomatic complexity assessment
            - Method complexity breakdown
            - Areas of high complexity
            - Simplification recommendations

            3. **TEST COVERAGE GAPS**
            - Methods lacking test coverage
            - Edge cases not covered
            - Exception handling gaps
            - Integration testing needs

            4. **POTENTIAL ISSUES & BUGS**
            - Null pointer risks
            - Memory leak potential
            - Logic errors
            - Input validation issues

            5. **SECURITY VULNERABILITIES**
            - Security risks identified
            - Input validation problems
            - Authentication issues
            - Data exposure risks

            6. **PERFORMANCE CONSIDERATIONS**
            - Performance bottlenecks
            - Inefficient algorithms
            - Memory usage issues
            - Optimization opportunities

            7. **DESIGN PATTERNS & ARCHITECTURE**
            - Design patterns used/missing
            - SOLID principles adherence
            - Architecture recommendations
            - Refactoring suggestions

            8. **MAINTAINABILITY ANALYSIS**
            - Code documentation quality
            - Naming conventions
            - Code duplication
            - Dependencies management

            Format each section with clear bullet points. Use simple, direct language without excessive formatting.
            """

            response = self.model.generate_content(prompt)
            analysis_text = response.text

            # Parse the AI response into structured data
            return self._parse_analysis_response(analysis_text)

        except Exception as e:
            print(f"AI Analysis error: {e}")
            return self._fallback_analysis()
    
    def generate_test_cases(self, code_content, file_info):
        """Generate comprehensive test cases using AI"""
        if not self.model:
            return [{'filename': 'error.txt', 'content': 'AI service not available'}]

        test_files = []
        
        for file_data in file_info:
            if self._is_testable_file(file_data['name']):
                try:
                    # Extract class and method information
                    analysis = self._analyze_source_code(file_data.get('content', ''))
                    
                    prompt = self._generate_test_prompt(file_data, analysis)
                    
                    response = self.model.generate_content(prompt)
                    test_code = response.text.strip()
                    
                    # Clean the generated test code
                    test_code = self._clean_generated_test_code(test_code, analysis)
                    
                    # Generate complete test file
                    complete_test = self._create_complete_test_file(test_code, analysis, file_data)
                    
                    test_filename = self._generate_test_filename(file_data['name'])
                    
                    test_files.append({
                        'filename': test_filename,
                        'content': complete_test,
                        'original_file': file_data['name']
                    })
                    
                except Exception as e:
                    print(f"Error generating tests for {file_data['name']}: {e}")
                    test_files.append({
                        'filename': f"error_{file_data['name']}.txt",
                        'content': f"Test generation failed: {str(e)}"
                    })
        
        return test_files

    def _generate_test_prompt(self, file_data, analysis):
        """Generate detailed test prompt based on your existing code"""
        class_name = analysis['class_name']
        method_list = ", ".join(analysis['method_names'])
        
        prompt = f"""You are an expert test automation engineer. Generate PERFECT JUnit 5 test methods for the provided Java code.

CRITICAL REQUIREMENTS:
1. PERFECT SYNTAX: Every test method must compile without errors
2. CORRECT EXPECTED VALUES: Calculate exact expected results - NO GUESSING
3. PRECISE ASSERTIONS: Use exact values, proper delta for floating-point comparisons
4. USE EXISTING INSTANCE: Use '{class_name.lower()}' instance from @BeforeEach - DO NOT create new objects
5. COMPLETE COVERAGE: Test positive cases, negative cases, edge cases, and exceptions
6. PROPER NAMING: testMethodName_condition_expectedResult format

EXAMPLE FORMAT:
@Test
@DisplayName("Test methodName with valid input")
void testMethodName_validInput_returnsExpectedResult() {{
    // Given
    double input = 4.0;
    double expected = 16.0; // 4 * 4 = 16
    
    // When
    double result = {class_name.lower()}.methodName(input);
    
    // Then
    assertEquals(expected, result, 0.0001);
}}

AVAILABLE METHODS: {method_list}

MATHEMATICAL ACCURACY REQUIREMENTS:
- Calculate ALL expected values manually and verify correctness
- For mathematical operations, show the calculation in comments

EXCEPTION TESTING FORMAT:
@Test
void testMethodName_invalidInput_throwsException() {{
    assertThrows(IllegalArgumentException.class, () -> {{
        {class_name.lower()}.methodName(invalidInput);
    }});
}}

OUTPUT REQUIREMENTS:
- Return ONLY test methods with @Test annotations
- NO class declaration, imports, or @BeforeEach method
- NO closing braces for class
- Perfect Java syntax in every line

SOURCE CODE TO TEST:
{file_data.get('content', '')[:8000]}

Generate comprehensive, mathematically accurate test methods now:"""
        
        return prompt

    def _analyze_source_code(self, source_code):
        """Analyze source code structure (from your existing code)"""
        class_name_match = re.search(r'public\s+class\s+(\w+)', source_code)
        class_name = class_name_match.group(1) if class_name_match else "UnknownClass"
        
        # Extract method signatures
        method_pattern = r'public\s+(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)'
        methods = re.findall(method_pattern, source_code)
        
        method_info = []
        for return_type, method_name in methods:
            if method_name != class_name:  # Skip constructor
                method_info.append({
                    'name': method_name,
                    'return_type': return_type
                })
        
        return {
            'class_name': class_name,
            'methods': method_info,
            'method_names': [m['name'] for m in method_info],
            'has_exceptions': 'throw' in source_code,
            'has_collections': 'List' in source_code or 'ArrayList' in source_code,
        }

    def _clean_generated_test_code(self, test_code, analysis):
        """Clean generated test code (from your existing code)"""
        if test_code.startswith("```java"):
            test_code = test_code[7:]
        elif test_code.startswith("```"):
            test_code = test_code[3:]
        if test_code.endswith("```"):
            test_code = test_code[:-3]

        lines = test_code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip imports, class declarations, @BeforeEach
            if (line.strip().startswith('import ') or 
                line.strip().startswith('public class') or
                line.strip().startswith('class ') or
                '@BeforeEach' in line or
                'void setUp()' in line):
                continue
            
            # Remove redundant object creation
            class_name = analysis['class_name']
            if f'{class_name} {class_name.lower()} = new {class_name}()' in line:
                continue
            
            # Replace standalone 'new ClassName()' with instance variable
            if f'new {class_name}()' in line:
                line = line.replace(f'new {class_name}()', class_name.lower())
            
            # Ensure using instance variable consistently
            if f'{class_name}.' in line:
                line = line.replace(f'{class_name}.', f'{class_name.lower()}.')
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def _create_complete_test_file(self, test_code, analysis, file_data):
        """Create complete test file with proper structure"""
        class_name = analysis['class_name']
        
        complete_test = f"""// Test file for {file_data['name']}
// Generated automatically using AI
// Coverage: Comprehensive unit tests

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

public class {class_name}Test {{
    private {class_name} {class_name.lower()};
    
    @BeforeEach
    void setUp() {{
        {class_name.lower()} = new {class_name}();
    }}

{test_code}
}}
"""
        return complete_test

    def _parse_analysis_response(self, analysis_text):
        """Parse AI analysis response into structured data"""
        # Extract quality score
        quality_score = 75  # Default
        score_match = re.search(r'Score:\s*(\d+)', analysis_text)
        if score_match:
            quality_score = int(score_match.group(1))

        # Split into sections
        sections = {
            'quality_assessment': self._extract_section(analysis_text, 'CODE QUALITY ASSESSMENT'),
            'complexity_analysis': self._extract_section(analysis_text, 'COMPLEXITY ANALYSIS'),
            'coverage_gaps': self._extract_section(analysis_text, 'TEST COVERAGE GAPS'),
            'potential_issues': self._extract_section(analysis_text, 'POTENTIAL ISSUES'),
            'security_vulnerabilities': self._extract_section(analysis_text, 'SECURITY VULNERABILITIES'),
            'performance_considerations': self._extract_section(analysis_text, 'PERFORMANCE CONSIDERATIONS'),
            'design_patterns': self._extract_section(analysis_text, 'DESIGN PATTERNS'),
            'maintainability': self._extract_section(analysis_text, 'MAINTAINABILITY')
        }

        return {
            'quality_score': quality_score,
            'detailed_analysis': analysis_text,
            'sections': sections,
            'summary': f"Code analysis completed with quality score: {quality_score}/100"
        }

    def _extract_section(self, text, section_name):
        """Extract specific section from analysis"""
        pattern = rf'{section_name}.*?(?=\d+\.\s*\*\*|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(0) if match else f"{section_name}: No specific issues found."

    def _fallback_analysis(self):
        """Fallback analysis when AI is not available"""
        return {
            'quality_score': 0,
            'detailed_analysis': 'AI service not available. Please check Vertex AI configuration.',
            'sections': {},
            'summary': 'Unable to perform AI-based analysis'
        }

    def _is_testable_file(self, filename):
        """Check if file can be tested"""
        testable_extensions = ['.py', '.java', '.js', '.ts', '.cpp', '.c', '.cs']
        return any(filename.endswith(ext) for ext in testable_extensions)

    def _generate_test_filename(self, original_filename):
        """Generate appropriate test filename"""
        name, ext = os.path.splitext(original_filename)
        if ext == '.py':
            return f"test_{name}.py"
        elif ext == '.java':
            return f"{name}Test.java"
        elif ext in ['.js', '.ts']:
            return f"{name}.test{ext}"
        else:
            return f"test_{name}{ext}"