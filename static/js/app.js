// Book RAG System - Frontend JavaScript
class BookRAGApp {
    constructor() {
        this.apiBase = '/api/v1';  // Use relative URL to avoid CORS issues
        this.token = localStorage.getItem('token');
        this.currentUser = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();
        if (this.token) {
            await this.loadUserData();
            this.showDashboard();
        } else {
            this.showAuth();
        }
    }

    setupEventListeners() {
        console.log('Setting up event listeners...');
        
        // Navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Auth forms
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        
        console.log('Login form found:', !!loginForm);
        console.log('Register form found:', !!registerForm);
        
        loginForm?.addEventListener('submit', (e) => {
            console.log('Login form submitted');
            this.handleLogin(e);
        });
        registerForm?.addEventListener('submit', (e) => {
            console.log('Register form submitted');
            this.handleRegister(e);
        });

        // Author dashboard
        document.getElementById('bookUploadForm')?.addEventListener('submit', (e) => this.handleBookUpload(e));
        
        // User dashboard
        document.getElementById('searchForm')?.addEventListener('submit', (e) => this.handleSearch(e));
        document.getElementById('ragForm')?.addEventListener('submit', (e) => this.handleRAG(e));

        // File upload drag & drop
        this.setupFileUpload();

        // Logout
        document.getElementById('logoutBtn')?.addEventListener('click', () => this.logout());
        
        console.log('Event listeners setup complete');
    }

    setupFileUpload() {
        const fileInput = document.getElementById('fileInput');
        const fileArea = document.getElementById('fileUploadArea');

        if (!fileArea) return;

        fileArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileArea.classList.add('dragover');
        });

        fileArea.addEventListener('dragleave', () => {
            fileArea.classList.remove('dragover');
        });

        fileArea.addEventListener('drop', (e) => {
            e.preventDefault();
            fileArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                this.updateFileDisplay(files[0]);
            }
        });

        fileArea.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.updateFileDisplay(e.target.files[0]);
            }
        });
    }

    updateFileDisplay(file) {
        const fileArea = document.getElementById('fileUploadArea');
        fileArea.innerHTML = `
            <div class="file-selected">
                <i class="fas fa-file-pdf" style="font-size: 2rem; color: #e53e3e; margin-bottom: 1rem;"></i>
                <p><strong>${file.name}</strong></p>
                <p>Size: ${(file.size / 1024 / 1024).toFixed(2)} MB</p>
                <p style="color: #48bb78; margin-top: 1rem;">✓ Ready to upload</p>
            </div>
        `;
    }

    async apiCall(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (this.token && !config.headers.Authorization) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'API request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            this.showLoading('Logging in...');
            const response = await this.apiCall('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({
                    username: formData.get('email'),
                    password: formData.get('password')
                })
            });

            this.token = response.access_token;
            localStorage.setItem('token', this.token);
            
            // Store user info
            this.currentUser = {
                id: response.user_id,
                role: response.user_role
            };
            localStorage.setItem('userRole', response.user_role);
            localStorage.setItem('userId', response.user_id);
            
            this.showDashboard();
            this.showAlert('Login successful!', 'success');
        } catch (error) {
            this.showAlert(error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async handleRegister(e) {
        console.log('handleRegister called');
        e.preventDefault();
        const formData = new FormData(e.target);
        
        console.log('Form data:', {
            email: formData.get('email'),
            username: formData.get('username'),
            role: formData.get('role')
        });
        
        try {
            this.showLoading('Creating account...');
            const response = await this.apiCall('/auth/register', {
                method: 'POST',
                body: JSON.stringify({
                    email: formData.get('email'),
                    username: formData.get('username'),
                    password: formData.get('password'),
                    role: formData.get('role')
                })
            });

            this.token = response.access_token;
            localStorage.setItem('token', this.token);
            
            // Store user info
            this.currentUser = {
                id: response.user_id,
                role: response.user_role
            };
            localStorage.setItem('userRole', response.user_role);
            localStorage.setItem('userId', response.user_id);
            
            this.showDashboard();
            this.showAlert('Account created successfully!', 'success');
        } catch (error) {
            console.error('Registration error:', error);
            this.showAlert(error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async loadUserData() {
        try {
            // Load user data from localStorage
            const userRole = localStorage.getItem('userRole');
            const userId = localStorage.getItem('userId');
            
            if (userRole && userId) {
                this.currentUser = {
                    id: parseInt(userId),
                    role: userRole
                };
            }
        } catch (error) {
            console.error('Failed to load user data:', error);
            this.logout();
        }
    }

    async handleBookUpload(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            this.showLoading('Uploading and processing book...');
            
            // Upload book (no need for author info, it's handled automatically)
            const uploadData = new FormData();
            uploadData.append('file', formData.get('file'));
            uploadData.append('title', formData.get('title'));
            uploadData.append('description', formData.get('description'));

            const response = await this.apiCall('/books/upload', {
                method: 'POST',
                headers: {}, // Remove Content-Type to let browser set it for FormData
                body: uploadData
            });

            this.showAlert('Book uploaded successfully! Processing started.', 'success');
            e.target.reset();
            document.getElementById('fileUploadArea').innerHTML = `
                <i class="fas fa-cloud-upload-alt" style="font-size: 3rem; color: #cbd5e0; margin-bottom: 1rem;"></i>
                <p>Drag & drop your PDF here or click to browse</p>
                <p style="color: #718096; font-size: 0.9rem;">Maximum file size: 100MB</p>
            `;
            
        } catch (error) {
            this.showAlert(error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async handleSearch(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const query = formData.get('query');
        
        try {
            this.showLoading('Searching...');
            const response = await this.apiCall('/search/semantic', {
                method: 'POST',
                body: JSON.stringify({
                    query: query,
                    limit: 10
                })
            });

            this.displaySearchResults(response.results, query);
        } catch (error) {
            this.showAlert(error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async handleRAG(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const query = formData.get('ragQuery');
        
        try {
            this.showLoading('Generating answer...');
            const response = await this.apiCall('/search/rag', {
                method: 'POST',
                body: JSON.stringify({
                    query: query,
                    max_chunks: 8
                })
            });

            // Log the raw API response
            console.log('📡 RAG API Response received:');
            console.log('  Total sources:', response.sources.length);
            response.sources.forEach((source, index) => {
                console.log(`  Backend Source ${index + 1}:`);
                console.log(`    book_id: ${source.book_id} (${typeof source.book_id})`);
                console.log(`    section_title: ${source.section_title}`);
                console.log(`    page_number: ${source.page_number} (${typeof source.page_number})`);
                console.log(`    text_length: ${source.text ? source.text.length : 'undefined'}`);
            });

            this.displayRAGResult(response, query);
        } catch (error) {
            this.showAlert(error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displaySearchResults(results, query) {
        const container = document.getElementById('searchResults');
        if (!results || results.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <h4><i class="fas fa-info-circle"></i> No Results Found</h4>
                    <p>No results found for "<strong>${query}</strong>".</p>
                    <p>This could mean:</p>
                    <ul>
                        <li>You haven't subscribed to any authors yet</li>
                        <li>The topic isn't covered in your subscribed authors' books</li>
                        <li>Try using different keywords or phrases</li>
                    </ul>
                    <p>Check the <strong>Authors</strong> tab to subscribe to authors and access their books.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <h3 style="margin-bottom: 1rem;">Search Results for "${query}"</h3>
            ${results.map((result, index) => `
                <div class="result-item" 
                     data-book-id="${result.book_id}" 
                     data-section-title="${result.section_title.replace(/"/g, '&quot;')}" 
                     data-page-number="${result.page_number}" 
                     data-text="${encodeURIComponent(result.text)}"
                     style="cursor: pointer;">
                    <div class="result-header">
                        <div class="result-score">Score: ${(result.score * 100).toFixed(1)}%</div>
                        <div class="result-book-info">
                            <strong>${result.book_title}</strong> by ${result.author_name}
                        </div>
                    </div>
                    <div class="result-text">${result.text}</div>
                    <div class="result-meta">
                        <strong>Section:</strong> ${result.section_title} | 
                        <strong>Page:</strong> ${result.page_number} |
                        <strong>Type:</strong> ${result.chunk_type} | 
                        <strong>Tokens:</strong> ${result.token_count}
                        <button class="pdf-preview-btn" data-result-index="${index}">
                            <i class="fas fa-file-pdf"></i> View PDF (Page ${result.page_number})
                        </button>
                    </div>
                </div>
            `).join('')}
        `;
        
        // Add event listeners for search result clicks
        const resultItems = container.querySelectorAll('.result-item');
        const resultButtons = container.querySelectorAll('.pdf-preview-btn');
        
        resultItems.forEach((item, index) => {
            item.addEventListener('click', (e) => {
                // Don't trigger if clicking on the button
                if (e.target.closest('.pdf-preview-btn')) return;
                
                this.handleSearchResultClick(item);
            });
        });
        
        resultButtons.forEach((button, index) => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const resultItem = button.closest('.result-item');
                this.handleSearchResultClick(resultItem);
            });
        });
    }

    displayRAGResult(response, query) {
        const container = document.getElementById('ragResults');
        
        // Debug the response structure
        console.log('🎨 Frontend displayRAGResult called:');
        console.log('  Total sources:', response.sources.length);
        response.sources.forEach((source, index) => {
            console.log(`  Frontend Source ${index + 1}:`);
            console.log(`    book_id: ${source.book_id} (${typeof source.book_id})`);
            console.log(`    section_title: ${source.section_title}`);
            console.log(`    page_number: ${source.page_number} (${typeof source.page_number})`);
            console.log(`    text length: ${source.text ? source.text.length : 'undefined'}`);
            console.log(`    text preview: ${source.text ? source.text.substring(0, 50) + '...' : 'NO TEXT'}`);
        });
        
        // Simplified formatting to avoid nested containers
        let formattedAnswer = response.answer
            // Normalize line breaks and spaces
            .replace(/\r\n/g, '\n')
            .replace(/\r/g, '\n')
            // Fix missing spaces after punctuation
            .replace(/\.([A-Z])/g, '. $1')
            .replace(/:([A-Z])/g, ': $1')
            .replace(/\?([A-Z])/g, '? $1')
            .replace(/!([A-Z])/g, '! $1')
            // Handle bold text formatting
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Simple paragraph breaks
            .replace(/\n\n+/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .trim();
        
        // Simple wrapper - no complex nested divs
        if (!formattedAnswer.startsWith('<p>')) {
            formattedAnswer = '<p>' + formattedAnswer + '</p>';
        }
        
        // Clean up empty paragraphs
        formattedAnswer = formattedAnswer.replace(/<p><\/p>/g, '');
        
        container.innerHTML = `
            <div class="card">
                <h3 style="margin-bottom: 1rem; color: #2d3748;">
                    <i class="fas fa-robot"></i> Answer for: "${query}"
                </h3>
                <div class="rag-answer">
                    ${formattedAnswer}
                </div>
                <div style="margin-top: 2rem;">
                    <h4 style="margin-bottom: 1rem; color: #4a5568;">
                        <i class="fas fa-book-open"></i> Sources (${response.total_chunks} chunks used):
                    </h4>
                    <div class="rag-sources">
                        ${response.sources.map((source, index) => {
                            // Debug each source before generating onclick
                            console.log(`🔨 Generating HTML for source ${index + 1}:`);
                            console.log(`   book_id: ${source.book_id} (${typeof source.book_id})`);
                            console.log(`   section_title: "${source.section_title}"`);
                            console.log(`   page_number: ${source.page_number} (${typeof source.page_number})`);
                            console.log(`   text_length: ${source.text ? source.text.length : 0}`);
                            
                            // Use data attributes instead of onclick to avoid escaping issues
                            const encodedText = encodeURIComponent(source.text || '');
                            
                            console.log(`🎯 Generated data for source ${index + 1}:`);
                            console.log(`   book_id: ${source.book_id}`);
                            console.log(`   page_number: ${source.page_number || 1}`);
                            console.log(`   encoded_text_length: ${encodedText.length}`);
                            
                            return `
                                <div class="rag-source-item" 
                                     data-book-id="${source.book_id}" 
                                     data-section-title="${source.section_title.replace(/"/g, '&quot;')}" 
                                     data-page-number="${source.page_number || 1}" 
                                     data-text="${encodedText}"
                                     style="cursor: pointer;">
                                    <div class="source-header">
                                        <strong>Source ${index + 1}:</strong> ${source.section_title}
                                    </div>
                                    ${source.text ? `
                                        <div class="source-preview">
                                            "${source.text.substring(0, 150)}${source.text.length > 150 ? '...' : ''}"
                                        </div>
                                    ` : ''}
                                    <div class="source-meta">
                                        <span class="source-score">Relevance: ${(source.score * 100).toFixed(1)}%</span>
                                        <span class="source-type">Type: ${source.chunk_type}</span>
                                        ${source.page_number ? `<span class="source-page">Page: ${source.page_number}</span>` : ''}
                                        <button class="source-view-btn" data-source-index="${index}">
                                            <i class="fas fa-external-link-alt"></i> View in PDF
                                        </button>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            </div>
        `;
        
        // Add event listeners for RAG source clicks
        console.log('🎧 Adding event listeners for RAG sources...');
        const sourceItems = container.querySelectorAll('.rag-source-item');
        const sourceButtons = container.querySelectorAll('.source-view-btn');
        
        sourceItems.forEach((item, index) => {
            item.addEventListener('click', (e) => {
                // Don't trigger if clicking on the button
                if (e.target.closest('.source-view-btn')) return;
                
                console.log(`🖱️ Source ${index + 1} clicked via event listener!`);
                this.handleSourceClick(item);
            });
        });
        
        sourceButtons.forEach((button, index) => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                console.log(`🖱️ Button ${index + 1} clicked via event listener!`);
                const sourceItem = button.closest('.rag-source-item');
                this.handleSourceClick(sourceItem);
            });
        });
    }

    handleSourceClick(sourceItem) {
        try {
            const bookId = parseInt(sourceItem.getAttribute('data-book-id'));
            const sectionTitle = sourceItem.getAttribute('data-section-title');
            const pageNumber = parseInt(sourceItem.getAttribute('data-page-number'));
            const encodedText = sourceItem.getAttribute('data-text');
            
            console.log('📋 handleSourceClick called with:');
            console.log('  bookId:', bookId, typeof bookId);
            console.log('  sectionTitle:', sectionTitle);
            console.log('  pageNumber:', pageNumber, typeof pageNumber);
            console.log('  encodedText length:', encodedText ? encodedText.length : 0);
            
            // Call openPdfViewer with the extracted data
            openPdfViewer(bookId, sectionTitle, pageNumber, encodedText);
        } catch (error) {
            console.error('❌ Error in handleSourceClick:', error);
            this.showAlert('Failed to open PDF: ' + error.message, 'error');
        }
    }

    handleSearchResultClick(resultItem) {
        try {
            const bookId = parseInt(resultItem.getAttribute('data-book-id'));
            const sectionTitle = resultItem.getAttribute('data-section-title');
            const pageNumber = parseInt(resultItem.getAttribute('data-page-number'));
            const encodedText = resultItem.getAttribute('data-text');
            
            console.log('🔍 handleSearchResultClick called with:');
            console.log('  bookId:', bookId, typeof bookId);
            console.log('  sectionTitle:', sectionTitle);
            console.log('  pageNumber:', pageNumber, typeof pageNumber);
            console.log('  encodedText length:', encodedText ? encodedText.length : 0);
            
            // Call openPdfViewer with the extracted data
            openPdfViewer(bookId, sectionTitle, pageNumber, encodedText);
        } catch (error) {
            console.error('❌ Error in handleSearchResultClick:', error);
            this.showAlert('Failed to open PDF: ' + error.message, 'error');
        }
    }

    async loadAuthors() {
        try {
            const response = await this.apiCall('/subscriptions/authors');
            this.displayAuthors(response);
        } catch (error) {
            this.showAlert('Failed to load authors', 'error');
        }
    }

    displayAuthors(authors) {
        const container = document.getElementById('authorsGrid');
        container.innerHTML = authors.map((author, index) => `
            <div class="author-card">
                <div class="author-avatar">${author.name.charAt(0)}</div>
                <div class="author-name">${author.name}</div>
                <div class="author-bio">${author.bio || 'No bio available'}</div>
                <div class="book-count">${author.book_count} books</div>
                <button class="btn ${author.is_subscribed ? 'btn-danger' : 'btn-primary'}" 
                        data-author-id="${author.id}" 
                        data-is-subscribed="${author.is_subscribed}"
                        data-author-index="${index}">
                    ${author.is_subscribed ? 'Unsubscribe' : 'Subscribe'}
                </button>
            </div>
        `).join('');
        
        // Add event listeners for subscription buttons
        const subscriptionButtons = container.querySelectorAll('button[data-author-id]');
        subscriptionButtons.forEach(button => {
            button.addEventListener('click', () => {
                const authorId = parseInt(button.getAttribute('data-author-id'));
                const isSubscribed = button.getAttribute('data-is-subscribed') === 'true';
                this.toggleSubscription(authorId, isSubscribed);
            });
        });
    }

    async toggleSubscription(authorId, isSubscribed) {
        try {
            if (isSubscribed) {
                await this.apiCall(`/subscriptions/${authorId}`, { method: 'DELETE' });
                this.showAlert('Unsubscribed successfully', 'success');
            } else {
                await this.apiCall('/subscriptions/', {
                    method: 'POST',
                    body: JSON.stringify({ author_id: authorId })
                });
                this.showAlert('Subscribed successfully', 'success');
            }
            this.loadAuthors(); // Refresh the list
        } catch (error) {
            this.showAlert(error.message, 'error');
        }
    }

    switchTab(tabName) {
        // Update active tab
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }

        // Show/hide content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        const tabContent = document.getElementById(`${tabName}Tab`);
        if (tabContent) {
            tabContent.classList.remove('hidden');
        }

        // Load data for specific tabs
        if (tabName === 'authors') {
            this.loadAuthors();
        }
    }

    showAuth() {
        document.getElementById('authSection').classList.remove('hidden');
        document.getElementById('dashboardSection').classList.add('hidden');
    }

    showDashboard() {
        document.getElementById('authSection').classList.add('hidden');
        document.getElementById('dashboardSection').classList.remove('hidden');
        
        // Show/hide tabs based on user role
        const uploadTab = document.querySelector('[data-tab="upload"]');
        if (this.currentUser?.role === 'author') {
            uploadTab.classList.remove('hidden');
            this.switchTab('upload');
        } else {
            uploadTab.classList.add('hidden');
            this.switchTab('search');
        }
    }

    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('userRole');
        localStorage.removeItem('userId');
        this.token = null;
        this.currentUser = null;
        this.showAuth();
        this.showAlert('Logged out successfully', 'info');
    }

    showLoading(message = 'Loading...') {
        const loading = document.getElementById('loadingOverlay');
        if (loading) {
            const loadingText = loading.querySelector('.loading-text');
            if (loadingText) {
                loadingText.textContent = message;
            }
            loading.classList.remove('hidden');
        }
    }

    hideLoading() {
        const loading = document.getElementById('loadingOverlay');
        if (loading) {
            loading.classList.add('hidden');
        }
    }

    showAlert(message, type = 'info') {
        let alertContainer = document.getElementById('alertContainer');
        if (!alertContainer) {
            // Create alert container if it doesn't exist
            alertContainer = document.createElement('div');
            alertContainer.id = 'alertContainer';
            document.body.insertBefore(alertContainer, document.body.firstChild);
        }
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.innerHTML = `
            ${message}
            <button onclick="this.parentElement.remove()" style="float: right; background: none; border: none; font-size: 1.2rem; cursor: pointer;">&times;</button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing app...');
    window.app = new BookRAGApp();
    console.log('App initialized:', window.app);
});

// PDF Viewer functionality
let pdfDoc = null;
let pageNum = 1;
let pageRendering = false;
let pageNumPending = null;
let scale = 1.0;
let canvas = null;
let ctx = null;
let highlightText = '';
let targetPage = 1;

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

window.openPdfViewer = async function(bookId, sectionTitle, pageNumber = 1, searchText = '') {
    try {
        console.log('📖 openPdfViewer called with parameters:');
        console.log('  Raw bookId:', bookId, '(type:', typeof bookId, ')');
        console.log('  Raw sectionTitle:', sectionTitle, '(type:', typeof sectionTitle, ')');
        console.log('  Raw pageNumber:', pageNumber, '(type:', typeof pageNumber, ')');
        console.log('  Raw searchText length:', searchText ? searchText.length : 0, '(type:', typeof searchText, ')');
        console.log('  Raw searchText preview:', searchText ? searchText.substring(0, 50) + '...' : 'None');
        
        console.log('📖 Opening PDF viewer:');
        console.log('  Book ID:', bookId);
        console.log('  Section:', sectionTitle);
        console.log('  Target Page:', pageNumber);
        console.log('  Search Text (raw):', searchText ? searchText.substring(0, 50) + '...' : 'None');
        
        // Decode the search text if it's encoded
        let decodedText = '';
        if (searchText) {
            try {
                decodedText = decodeURIComponent(searchText);
                console.log('  ✅ Successfully decoded text, length:', decodedText.length);
            } catch (e) {
                // If decoding fails, use the text as-is (might already be decoded)
                decodedText = searchText;
                console.log('  ⚠️ Decoding failed, using raw text, length:', decodedText.length);
            }
        }
        
        // Store highlight information
        highlightText = decodedText;
        targetPage = pageNumber || 1;
        
        console.log('  Decoded text length:', highlightText.length);
        console.log('  Decoded text preview:', highlightText ? highlightText.substring(0, 50) + '...' : 'None');
        console.log('  Stored target page:', targetPage);
        
        // Show modal
        document.getElementById('pdfViewerModal').classList.remove('hidden');
        document.getElementById('pdfViewerTitle').textContent = `PDF Viewer - ${sectionTitle} (Page ${targetPage})`;
        
        // Initialize canvas
        canvas = document.getElementById('pdfCanvas');
        ctx = canvas.getContext('2d');
        
        // Load PDF
        const pdfUrl = `/api/v1/books/${bookId}/pdf`;
        console.log('  Loading PDF from:', pdfUrl);
        
        // Add authorization header
        const response = await fetch(pdfUrl, {
            headers: {
                'Authorization': `Bearer ${window.app.token}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load PDF: ${response.status} ${response.statusText}`);
        }
        
        const pdfArrayBuffer = await response.arrayBuffer();
        pdfDoc = await pdfjsLib.getDocument({data: pdfArrayBuffer}).promise;
        
        console.log('  PDF loaded, total pages:', pdfDoc.numPages);
        console.log('  Will navigate to page:', Math.min(targetPage, pdfDoc.numPages));
        
        // Navigate to target page
        pageNum = Math.min(targetPage, pdfDoc.numPages);
        scale = 1.0;
        
        console.log('  Final page number set to:', pageNum);
        
        // Render target page
        renderPage(pageNum);
        
        // Update controls
        updatePageInfo();
        
    } catch (error) {
        console.error('Error opening PDF:', error);
        window.app.showAlert('Failed to load PDF: ' + error.message, 'error');
    }
};

function renderPage(num) {
    pageRendering = true;
    console.log('🎨 Rendering page:', num, 'Target page:', targetPage, 'Has highlight text:', !!highlightText);
    
    // Get page
    pdfDoc.getPage(num).then(function(page) {
        const viewport = page.getViewport({scale: scale});
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        // Clear any existing highlights
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Render PDF page into canvas context
        const renderContext = {
            canvasContext: ctx,
            viewport: viewport
        };
        
        const renderTask = page.render(renderContext);
        
        // Wait for rendering to finish
        renderTask.promise.then(function() {
            pageRendering = false;
            
            console.log('✅ Page rendered. Checking for highlighting...');
            console.log('  Current page:', num, 'Target page:', targetPage);
            console.log('  Highlight text:', highlightText ? highlightText.substring(0, 50) + '...' : 'None');
            
            // Highlight text if we're on the target page
            if (num === targetPage && highlightText) {
                console.log('🎯 Starting highlighting process...');
                // Add a small delay to ensure rendering is complete
                setTimeout(() => {
                    highlightTextOnPageImproved(page, viewport);
                }, 100);
            } else {
                console.log('❌ No highlighting - Page mismatch or no text');
            }
            
            if (pageNumPending !== null) {
                // New page rendering is pending
                renderPage(pageNumPending);
                pageNumPending = null;
            }
        });
    });
    
    // Update page counters
    updatePageInfo();
}

async function highlightTextOnPageImproved(page, viewport) {
    try {
        // Get text content with more detailed positioning
        const textContent = await page.getTextContent({
            normalizeWhitespace: false,
            disableCombineTextItems: false
        });
        
        // Prepare search terms from the highlight text
        const searchWords = highlightText.toLowerCase()
            .split(/\s+/)
            .filter(word => word.length > 2)
            .map(word => word.replace(/[^\w]/g, '')); // Remove punctuation
        
        const highlights = [];
        
        // Process each text item
        for (let i = 0; i < textContent.items.length; i++) {
            const item = textContent.items[i];
            const text = item.str.toLowerCase().replace(/[^\w\s]/g, ''); // Clean text for matching
            
            // Check if this text item contains any search words
            const matchingWords = searchWords.filter(word => text.includes(word));
            
            if (matchingWords.length > 0) {
                // Calculate precise positioning
                const transform = item.transform;
                
                // Extract position and scale from transformation matrix
                const scaleX = transform[0];
                const scaleY = transform[3];
                const translateX = transform[4];
                const translateY = transform[5];
                
                // Convert PDF coordinates to canvas coordinates
                const x = translateX * viewport.scale;
                const y = (viewport.height - translateY) * viewport.scale;
                
                // Calculate text dimensions more accurately
                const fontSize = Math.abs(scaleY) * viewport.scale;
                const textWidth = item.width * viewport.scale;
                
                // Adjust for text baseline (text is drawn from baseline, not top)
                const adjustedY = y - fontSize * 0.8; // Approximate baseline adjustment
                
                highlights.push({
                    x: Math.round(x),
                    y: Math.round(adjustedY),
                    width: Math.round(textWidth),
                    height: Math.round(fontSize),
                    text: item.str,
                    matchingWords: matchingWords
                });
            }
        }
        
        // If we didn't find many matches with individual words, try phrase matching
        if (highlights.length < 3 && highlightText.length > 10) {
            // Try to find text items that are part of longer phrases
            const phrases = highlightText.toLowerCase().split(/[.!?]+/).filter(p => p.trim().length > 5);
            
            for (const phrase of phrases) {
                const phraseWords = phrase.trim().split(/\s+/).slice(0, 3); // First 3 words of phrase
                
                for (let i = 0; i < textContent.items.length - phraseWords.length; i++) {
                    let phraseMatch = true;
                    const phraseItems = [];
                    
                    for (let j = 0; j < phraseWords.length; j++) {
                        const item = textContent.items[i + j];
                        if (!item || !item.str.toLowerCase().includes(phraseWords[j])) {
                            phraseMatch = false;
                            break;
                        }
                        phraseItems.push(item);
                    }
                    
                    if (phraseMatch && phraseItems.length > 0) {
                        // Highlight the entire phrase area
                        const firstItem = phraseItems[0];
                        const lastItem = phraseItems[phraseItems.length - 1];
                        
                        const transform = firstItem.transform;
                        const x = transform[4] * viewport.scale;
                        const y = (viewport.height - transform[5]) * viewport.scale;
                        const fontSize = Math.abs(transform[3]) * viewport.scale;
                        
                        // Calculate width spanning all items
                        const lastTransform = lastItem.transform;
                        const lastX = lastTransform[4] * viewport.scale;
                        const lastWidth = lastItem.width * viewport.scale;
                        const totalWidth = (lastX + lastWidth) - x;
                        
                        highlights.push({
                            x: Math.round(x),
                            y: Math.round(y - fontSize * 0.8),
                            width: Math.round(totalWidth),
                            height: Math.round(fontSize),
                            text: phraseItems.map(item => item.str).join(' '),
                            matchingWords: phraseWords
                        });
                    }
                }
            }
        }
        
        // Draw highlights with improved styling
        if (highlights.length > 0) {
            drawHighlights(highlights);
            console.log(`✨ Highlighted ${highlights.length} text matches on page ${pageNum}`);
        } else {
            console.log(`🔍 No matching text found on page ${pageNum} for: "${highlightText.substring(0, 50)}..."`);
        }
        
    } catch (error) {
        console.error('❌ Error highlighting text:', error);
    }
}

function drawHighlights(highlights) {
    ctx.save();
    
    // Draw highlight backgrounds
    ctx.globalAlpha = 0.35;
    ctx.fillStyle = '#ffeb3b'; // Material Design Yellow
    
    highlights.forEach(highlight => {
        // Draw rounded rectangle for better appearance
        const radius = 2;
        drawRoundedRect(
            ctx,
            highlight.x - 2, // Small padding
            highlight.y - 2,
            highlight.width + 4,
            highlight.height + 4,
            radius
        );
    });
    
    // Draw subtle borders
    ctx.globalAlpha = 0.7;
    ctx.strokeStyle = '#ffc107'; // Slightly darker yellow
    ctx.lineWidth = 1;
    
    highlights.forEach(highlight => {
        const radius = 2;
        drawRoundedRectStroke(
            ctx,
            highlight.x - 2,
            highlight.y - 2,
            highlight.width + 4,
            highlight.height + 4,
            radius
        );
    });
    
    ctx.restore();
}

function drawRoundedRect(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
    ctx.fill();
}

function drawRoundedRectStroke(ctx, x, y, width, height, radius) {
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + width - radius, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
    ctx.lineTo(x + width, y + height - radius);
    ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    ctx.lineTo(x + radius, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
    ctx.stroke();
}



function queueRenderPage(num) {
    if (pageRendering) {
        pageNumPending = num;
    } else {
        renderPage(num);
    }
}

function prevPage() {
    if (pageNum <= 1) {
        return;
    }
    pageNum--;
    queueRenderPage(pageNum);
}

function nextPage() {
    if (pageNum >= pdfDoc.numPages) {
        return;
    }
    pageNum++;
    queueRenderPage(pageNum);
}

function zoomIn() {
    scale += 0.25;
    queueRenderPage(pageNum);
    updateZoomLevel();
}

function zoomOut() {
    if (scale <= 0.5) {
        return;
    }
    scale -= 0.25;
    queueRenderPage(pageNum);
    updateZoomLevel();
}

function updatePageInfo() {
    if (pdfDoc) {
        document.getElementById('pageInfo').textContent = `Page ${pageNum} of ${pdfDoc.numPages}`;
        
        // Update button states
        document.getElementById('prevPage').disabled = pageNum <= 1;
        document.getElementById('nextPage').disabled = pageNum >= pdfDoc.numPages;
    }
}

function updateZoomLevel() {
    document.getElementById('zoomLevel').textContent = `${Math.round(scale * 100)}%`;
    document.getElementById('zoomOut').disabled = scale <= 0.5;
}

function closePdfViewer() {
    document.getElementById('pdfViewerModal').classList.add('hidden');
    
    // Clean up
    if (canvas) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    pdfDoc = null;
    pageNum = 1;
    scale = 1.0;
    highlightText = '';
    targetPage = 1;
}

// Keyboard shortcuts for PDF viewer
document.addEventListener('keydown', function(e) {
    const modal = document.getElementById('pdfViewerModal');
    if (!modal.classList.contains('hidden')) {
        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                prevPage();
                break;
            case 'ArrowRight':
                e.preventDefault();
                nextPage();
                break;
            case 'Escape':
                e.preventDefault();
                closePdfViewer();
                break;
            case '+':
            case '=':
                e.preventDefault();
                zoomIn();
                break;
            case '-':
                e.preventDefault();
                zoomOut();
                break;
        }
    }
});
// Function to open PDF from RAG sources
async function openPdfFromSource(bookId, sectionTitle, pageNumber = 1, sourceText = '') {
    try {
        console.log('🔍 Opening PDF from source:');
        console.log('  Book ID:', bookId);
        console.log('  Section:', sectionTitle);
        console.log('  Page Number:', pageNumber);
        console.log('  Source Text Length:', sourceText ? decodeURIComponent(sourceText).length : 0);
        
        // Open PDF to the specific page with the source text highlighted
        const textToHighlight = sourceText ? decodeURIComponent(sourceText) : sectionTitle;
        console.log('  Text to highlight:', textToHighlight.substring(0, 100) + '...');
        
        await openPdfViewer(bookId, sectionTitle, pageNumber, textToHighlight);
    } catch (error) {
        console.error('Error opening PDF from source:', error);
        window.app.showAlert('Failed to open PDF: ' + error.message, 'error');
    }
}