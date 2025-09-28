class ManualModeApp {
    constructor() {
        this.currentAnalysis = null;
        this.currentFiles = [];
        this.currentCacheKey = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Mode toggle
        document.getElementById('modeToggle').addEventListener('change', this.handleModeToggle.bind(this));
        document.getElementById('generateDocumentBtn').addEventListener('click', this.handleGenerateDocument.bind(this));

        
        // Manual mode functionality
        document.getElementById('analyzeBtn').addEventListener('click', this.handleAnalyze.bind(this));
        document.getElementById('generateTestBtn').addEventListener('click', this.handleGenerateTests.bind(this));
        document.getElementById('fileUpload').addEventListener('change', this.handleFileUpload.bind(this));
    }

    handleModeToggle(e) {
        if (e.target.checked) {
            // Switch to Automatic mode
            window.location.href = '/automatic';
        }
    }

    async handleAnalyze() {
        const gitUrl = document.getElementById('gitUrl').value.trim();
        const accessToken = document.getElementById('accessToken').value.trim();
        const manualCode = document.getElementById('manualCode').value.trim();

        if (!gitUrl && !manualCode && this.currentFiles.length === 0) {
            this.showError('Please provide code via Git URL, manual input, or file upload.');
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    git_url: gitUrl,
                    access_token: accessToken,
                    manual_code: manualCode
                })
            });

            const result = await response.json();

            if (result.success) {
                this.currentAnalysis = result.analysis;
                this.currentCacheKey = result.cache_key;
                this.displayAnalysis(result.analysis);
                document.getElementById('generateTestBtn').disabled = false;
            } else {
                this.showError(result.error || 'Analysis failed');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async handleFileUpload() {
        const fileInput = document.getElementById('fileUpload');
        const files = fileInput.files;

        if (files.length === 0) return;

        this.showLoading(true);

        try {
            const formData = new FormData();
            for (let file of files) {
                formData.append('file', file);
            }

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.currentAnalysis = result.analysis;
                this.currentCacheKey = result.cache_key;
                this.displayAnalysis(result.analysis);
                document.getElementById('generateTestBtn').disabled = false;
            } else {
                this.showError(result.error || 'File upload failed');
            }
        } catch (error) {
            this.showError('Upload error: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async handleGenerateTests() {
        if (!this.currentCacheKey) {
            this.showError('Please analyze code first');
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch('/generate-tests', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    cache_key: this.currentCacheKey
                })
            });

            const result = await response.json();

            if (result.success) {
                this.displayTestResults(result.test_files, result.download_url, result.total_files);
            } else {
                this.showError(result.error || 'Test generation failed');
            }
        } catch (error) {
            this.showError('Generation error: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async handleGenerateDocument() {
        if (!this.currentCacheKey) {
            this.showError('Please analyze code first');
            return;
        }
    
        const documentBtn = document.getElementById('generateDocumentBtn');
        const originalText = documentBtn.innerHTML;
        
        // Show loading state
        documentBtn.classList.add('loading');
        documentBtn.disabled = true;
        documentBtn.innerHTML = '⏳ Generating Document...';
    
        try {
            const response = await fetch('/generate-document', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    cache_key: this.currentCacheKey
                })
            });
    
            const result = await response.json();
    
            if (result.success) {
                // Create download link
                const downloadLink = document.createElement('a');
                downloadLink.href = result.download_url;
                downloadLink.download = result.filename;
                downloadLink.style.display = 'none';
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
                
                this.showDocumentSuccess(result.filename);
            } else {
                this.showError(result.error || 'Document generation failed');
            }
        } catch (error) {
            this.showError('Document generation error: ' + error.message);
        } finally {
            // Reset button state
            documentBtn.classList.remove('loading');
            documentBtn.disabled = false;
            documentBtn.innerHTML = originalText;
        }
    }
    
    // Add this method to show success message
    showDocumentSuccess(filename) {
        const documentSection = document.querySelector('.document-section');
        
        // Create success message
        const successMsg = document.createElement('div');
        successMsg.className = 'document-success';
        successMsg.style.cssText = `
            background-color: #4CAF50;
            color: white;
            padding: 10px;
            border-radius: 6px;
            margin-top: 10px;
            text-align: center;
            font-size: 0.9rem;
        `;
        successMsg.innerHTML = `✅ Document "${filename}" downloaded successfully!`;
        
        // Remove existing success message
        const existingMsg = documentSection.querySelector('.document-success');
        if (existingMsg) {
            existingMsg.remove();
        }
        
        documentSection.appendChild(successMsg);
        
        // Remove message after 5 seconds
        setTimeout(() => {
            if (successMsg.parentNode) {
                successMsg.remove();
            }
        }, 5000);
    }
    

    displayAnalysis(analysis) {
        const analysisResult = document.getElementById('analysisResult');
        
        // Determine quality score class
        let scoreClass = 'quality-score-low';
        if (analysis.quality_score >= 80) scoreClass = 'quality-score-high';
        else if (analysis.quality_score >= 60) scoreClass = 'quality-score-medium';
        
        // Create quality score section
        const qualityScoreHtml = `
            <div class="quality-score-container">
                <div class="quality-score-info">
                    <h4 style="margin: 0; color: #e0e0e0;">Code Quality Assessment</h4>
                    <span class="quality-score-compact ${scoreClass}">${analysis.quality_score}/100</span>
                </div>
            </div>
        `;
        
        // Create summary section
        const summaryHtml = `
            <div class="analysis-summary">
                <h4>Summary</h4>
                <p>${analysis.summary}</p>
            </div>
        `;
        
        // Parse the detailed analysis
        const parsedSections = this.parseDetailedAnalysis(analysis.detailed_analysis);
        
        // Create collapsible sections
        let sectionsHtml = '<div class="analysis-sections-container">';
        
        parsedSections.forEach((section, index) => {
            if (section.content.trim()) {
                const sectionId = `section-${index}`;
                
                sectionsHtml += `
                    <div class="analysis-section-collapsible">
                        <div class="analysis-section-header" onclick="app.toggleSection('${sectionId}')">
                            <h4 class="analysis-section-title">${section.title}</h4>
                            <span class="analysis-section-toggle" id="${sectionId}-toggle">▼</span>
                        </div>
                        <div class="analysis-section-content" id="${sectionId}">
                            <div class="analysis-section-body">
                                ${section.content}
                            </div>
                        </div>
                    </div>
                `;
            }
        });
        
        sectionsHtml += '</div>';
        
        // Combine all sections
        const finalHtml = qualityScoreHtml + summaryHtml + sectionsHtml;
        
        analysisResult.innerHTML = finalHtml;
        // Enable document generation button
        document.getElementById('generateDocumentBtn').disabled = false;
    }

    parseDetailedAnalysis(detailedAnalysis) {
        const sections = [];
        const lines = detailedAnalysis.split('\n');
        let currentSection = { title: 'General Analysis', content: '' };
        
        for (let line of lines) {
            line = line.trim();
            
            // Check if this is a section header
            if (this.isSectionHeader(line)) {
                // Save previous section if it has content
                if (currentSection.content.trim()) {
                    sections.push({
                        title: currentSection.title,
                        content: this.formatSectionContent(currentSection.content)
                    });
                }
                
                // Start new section
                currentSection = {
                    title: this.cleanSectionTitle(line),
                    content: ''
                };
            } else {
                // Add content to current section
                if (line && !line.startsWith('#')) {
                    currentSection.content += line + '\n';
                }
            }
        }
        
        // Add the last section
        if (currentSection.content.trim()) {
            sections.push({
                title: currentSection.title,
                content: this.formatSectionContent(currentSection.content)
            });
        }
        
        return sections;
    }

    isSectionHeader(line) {
        return (
            line.match(/^\d+\.\s*\*\*/) ||
            line.match(/^\d+\.\s*[A-Z\s&]{10,}$/) ||
            line.match(/^#{1,3}\s*\d+\./) ||
            line.match(/^[A-Z\s&]{15,}$/)
        );
    }

    cleanSectionTitle(title) {
        return title
            .replace(/^\d+\.\s*/, '')
            .replace(/\*\*/g, '')
            .replace(/#{1,3}\s*/, '')
            .replace(/[_]/g, ' ')
            .trim()
            .toLowerCase()
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    formatSectionContent(content) {
        if (!content || !content.trim()) {
            return '<p style="color: #888; font-style: italic;">No specific analysis available for this section.</p>';
        }
        
        let cleanContent = content
            .replace(/#{1,6}\s*/g, '')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .trim();
        
        const lines = cleanContent.split('\n').filter(line => line.trim());
        let formattedContent = '';
        let inList = false;
        
        for (let line of lines) {
            line = line.trim();
            
            if (!line) continue;
            
            if (line.startsWith('-') || line.startsWith('•') || line.match(/^\d+\./)) {
                if (!inList) {
                    formattedContent += '<ul class="analysis-list">';
                    inList = true;
                }
                
                const listItem = line.replace(/^[-•]\s*/, '').replace(/^\d+\.\s*/, '');
                formattedContent += `<li>${listItem}</li>`;
            } else {
                if (inList) {
                    formattedContent += '</ul>';
                    inList = false;
                }
                
                if (line.length > 5) {
                    formattedContent += `<p>${line}</p>`;
                }
            }
        }
        
        if (inList) {
            formattedContent += '</ul>';
        }
        
        return formattedContent || '<p style="color: #888; font-style: italic;">No detailed analysis available.</p>';
    }

    toggleSection(sectionId) {
        const content = document.getElementById(sectionId);
        const toggle = document.getElementById(sectionId + '-toggle');
        
        if (content.classList.contains('expanded')) {
            content.classList.remove('expanded');
            toggle.classList.remove('expanded');
        } else {
            content.classList.add('expanded');
            toggle.classList.add('expanded');
        }
    }

    displayTestResults(testFiles, downloadUrl, totalFiles) {
        const testResults = document.getElementById('testResults');
        
        const html = `
            <div class="download-section">
                <div>
                    <strong>✅ Generated ${totalFiles} test files</strong>
                    <p style="margin: 5px 0; color: #b0b0b0; font-size: 0.9rem;">
                        ${testFiles.map(f => f.filename).join(', ')}
                    </p>
                </div>
                <a href="${downloadUrl}" class="download-all-btn" download>
                    📥 Download All Tests
                </a>
            </div>
        `;
        
        testResults.innerHTML = html;
    }

    showError(message) {
        const analysisResult = document.getElementById('analysisResult');
        analysisResult.innerHTML = `
            <div style="background-color: #f44336; color: white; padding: 20px; border-radius: 8px; text-align: center;">
                <h4 style="margin: 0 0 10px 0;">❌ Error</h4>
                <p style="margin: 0;">${message}</p>
            </div>
        `;
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }
}

// Initialize app when page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ManualModeApp();
});