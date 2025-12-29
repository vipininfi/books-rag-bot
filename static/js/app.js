// BookRAG Pro - Frontend JavaScript
class BookRAGApp {
    constructor() {
        this.apiBase = '/api/v1';
        this.token = localStorage.getItem('token');
        this.currentUser = null;
        
        // Voice functionality
        this.recognition = null;
        this.speechSynthesis = window.speechSynthesis;
        this.currentUtterance = null;
        this.isListening = false;
        this.isSpeaking = false;
        this.speechTimeout = null;
        this.ttsTimeout = null;
        this.ttsStarted = false;
        this.userStoppedSpeech = false;
        
        this.init();
    }

    async init() {
        console.log('App init started');
        
        console.log('Token from localStorage:', this.token);
        
        if (this.token) {
            console.log('Token found, validating and loading user data');
            try {
                await this.loadUserData();
                
                // Validate that we have proper user data
                if (this.currentUser && this.currentUser.id && this.currentUser.role) {
                    console.log('Valid user data found, showing dashboard');
                    this.showDashboard();
                } else {
                    console.log('Invalid user data, clearing token and showing auth');
                    this.clearAuthData();
                    this.showAuth();
                }
            } catch (error) {
                console.error('Error loading user data:', error);
                // If there's an error loading user data, clear token and show auth
                this.clearAuthData();
                this.showAuth();
            }
        } else {
            console.log('No token found, showing auth');
            this.showAuth();
        }
        
        // Setup event listeners AFTER determining which view to show
        this.setupEventListeners();
        this.checkMicrophonePermission();
        
        // Add page unload cleanup
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
        
        window.addEventListener('unload', () => {
            this.cleanup();
        });
        
        console.log('App init completed');
    }

    clearAuthData() {
        console.log('Clearing all auth data');
        localStorage.removeItem('token');
        localStorage.removeItem('userRole');
        localStorage.removeItem('userId');
        localStorage.removeItem('username');
        localStorage.removeItem('email');
        this.token = null;
        this.currentUser = null;
    }


    setupSidebarNavigation() {
        console.log('Setting up sidebar navigation...');
        
        // Menu toggle
        const menuToggle = document.getElementById('menuToggle');
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.querySelector('.main-content');
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebarBackdrop = document.getElementById('sidebarBackdrop');

        console.log('Elements found:', {
            menuToggle: !!menuToggle,
            sidebar: !!sidebar,
            mainContent: !!mainContent,
            sidebarToggle: !!sidebarToggle,
            sidebarBackdrop: !!sidebarBackdrop
        });

        const toggleSidebar = (show) => {
            console.log('toggleSidebar called with show:', show);
            if (sidebar) {
                if (show) {
                    sidebar.classList.add('active');
                } else {
                    sidebar.classList.remove('active');
                }
            }
            if (sidebarBackdrop) {
                if (show) {
                    sidebarBackdrop.classList.add('active');
                } else {
                    sidebarBackdrop.classList.remove('active');
                }
            }
            if (mainContent) {
                if (show) {
                    mainContent.classList.add('sidebar-open');
                } else {
                    mainContent.classList.remove('sidebar-open');
                }
            }
        };

        if (menuToggle) {
            menuToggle.addEventListener('click', () => {
                console.log('Menu toggle clicked');
                const isActive = sidebar?.classList.contains('active');
                toggleSidebar(!isActive);
            });
            console.log('Menu toggle listener attached');
        }

        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                console.log('Sidebar close button clicked');
                toggleSidebar(false);
            });
            console.log('Sidebar toggle listener attached');
        }

        if (sidebarBackdrop) {
            sidebarBackdrop.addEventListener('click', () => {
                console.log('Backdrop clicked');
                toggleSidebar(false);
            });
            console.log('Backdrop listener attached');
        }

        // Navigation items
        const navItems = document.querySelectorAll('.nav-item');
        console.log('Found nav items:', navItems.length);
        
        navItems.forEach((item, index) => {
            const tab = item.dataset.tab;
            console.log(`Nav item ${index}: tab="${tab}"`);
            
            item.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Nav item clicked:', tab);
                if (tab) {
                    this.switchTab(tab);
                    // Close sidebar on mobile
                    if (window.innerWidth <= 1024) {
                        toggleSidebar(false);
                    }
                }
            });
        });

        // User menu dropdown
        const userMenuBtn = document.getElementById('userMenuBtn');
        const userDropdown = document.getElementById('userDropdown');

        console.log('User menu elements:', {
            userMenuBtn: !!userMenuBtn,
            userDropdown: !!userDropdown
        });

        if (userMenuBtn && userDropdown) {
            userMenuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                console.log('User menu clicked');
                userDropdown.classList.toggle('active');
                console.log('Dropdown active:', userDropdown.classList.contains('active'));
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!userMenuBtn.contains(e.target) && !userDropdown.contains(e.target)) {
                    userDropdown.classList.remove('active');
                }
            });

            // User dropdown navigation
            const dropdownItems = userDropdown.querySelectorAll('a[data-tab]');
            console.log('Found dropdown items:', dropdownItems.length);
            
            dropdownItems.forEach((item, index) => {
                const tab = item.dataset.tab;
                console.log(`Dropdown item ${index}: tab="${tab}"`);
                
                item.addEventListener('click', (e) => {
                    e.preventDefault();
                    console.log('Dropdown item clicked:', tab);
                    if (tab) {
                        this.switchTab(tab);
                        userDropdown.classList.remove('active');
                    }
                });
            });
        }
        
        console.log('Sidebar navigation setup complete');
    }

    switchTab(tabName) {
        console.log('Switching to tab:', tabName);
        
        // Update sidebar navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        const activeNavItem = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }

        // Update page title
        const titles = {
            'search': { title: 'Search Books', subtitle: 'Find information across your subscribed authors\' books' },
            'rag': { title: 'AI Assistant', subtitle: 'Ask questions and get AI-powered answers' },
            'authors': { title: 'Discover Authors', subtitle: 'Browse and subscribe to authors' },
            'upload': { title: 'Upload Books', subtitle: 'Share your books with subscribers' },
            'profile': { title: 'Profile Settings', subtitle: 'Manage your account information' },
            'subscriptions': { title: 'My Subscriptions', subtitle: 'Manage your author subscriptions' },
            'analytics': { title: 'Usage Analytics', subtitle: 'Track your platform usage' },
            'my-books': { title: 'My Books', subtitle: 'Manage your uploaded books' }
        };

        const titleInfo = titles[tabName] || { title: 'Dashboard', subtitle: 'Welcome to BookRAG Pro' };
        document.getElementById('pageTitle').textContent = titleInfo.title;
        document.getElementById('pageSubtitle').textContent = titleInfo.subtitle;

        // Show/hide content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        const tabContent = document.getElementById(`${tabName}Tab`);
        if (tabContent) {
            tabContent.classList.remove('hidden');
        }

        // Load data for specific tabs
        this.loadTabData(tabName);
    }

    async loadTabData(tabName) {
        switch (tabName) {
            case 'authors':
                await this.loadAuthors();
                break;
            case 'profile':
                await this.loadProfile();
                break;
            case 'subscriptions':
                await this.loadSubscriptions();
                break;
            case 'analytics':
                await this.loadAnalytics();
                break;
            case 'my-books':
                if (this.currentUser?.role === 'author') {
                    await this.loadMyBooks();
                }
                break;
        }
    }

    async loadProfile() {
        try {
            const response = await this.apiCall('/users/profile');
            
            // Load current user data into profile form
            document.getElementById('profileUsername').value = response.username || '';
            document.getElementById('profileEmail').value = response.email || '';
            
            // Show/hide author bio field based on role
            const authorBioGroup = document.getElementById('authorBioGroup');
            if (response.role === 'author') {
                authorBioGroup.style.display = 'block';
                document.getElementById('profileBio').value = response.author_bio || '';
            } else {
                authorBioGroup.style.display = 'none';
            }
        } catch (error) {
            console.error('Failed to load profile:', error);
            this.showAlert('Failed to load profile data', 'error');
        }
    }

    async handleProfileUpdate(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        // Validate password confirmation
        const newPassword = formData.get('newPassword');
        const confirmPassword = formData.get('confirmPassword');
        
        if (newPassword && newPassword !== confirmPassword) {
            this.showAlert('New passwords do not match', 'error');
            return;
        }
        
        try {
            this.showLoading('Updating profile...');
            
            const updateData = {
                username: formData.get('username'),
                email: formData.get('email')
            };
            
            // Add bio for authors
            if (this.currentUser?.role === 'author') {
                updateData.bio = formData.get('bio');
            }
            
            // Add password fields if provided
            const currentPassword = formData.get('currentPassword');
            if (currentPassword) {
                updateData.current_password = currentPassword;
                if (newPassword) {
                    updateData.new_password = newPassword;
                }
            }
            
            const response = await this.apiCall('/users/profile', {
                method: 'PUT',
                body: JSON.stringify(updateData)
            });
            
            // Update stored user data
            this.currentUser.username = response.username;
            this.currentUser.email = response.email;
            localStorage.setItem('username', response.username);
            localStorage.setItem('email', response.email);
            
            // Update UI
            this.updateUserInfo();
            
            // Clear password fields
            document.getElementById('currentPassword').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('confirmPassword').value = '';
            
            this.showAlert('Profile updated successfully!', 'success');
            
        } catch (error) {
            this.showAlert(error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async loadSubscriptions() {
        try {
            const response = await this.apiCall('/subscriptions/');
            this.displaySubscriptions(response);
        } catch (error) {
            console.error('Failed to load subscriptions:', error);
            this.showAlert('Failed to load subscriptions', 'error');
        }
    }

    displaySubscriptions(subscriptions) {
        const container = document.getElementById('subscriptionsList');
        
        if (!subscriptions || subscriptions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-heart" style="font-size: 3rem; color: var(--text-secondary); margin-bottom: 1rem;"></i>
                    <h3>No Subscriptions Yet</h3>
                    <p>You haven't subscribed to any authors yet. Browse the Authors tab to discover and subscribe to authors.</p>
                    <button class="btn btn-primary" onclick="app.switchTab('authors')">
                        <i class="fas fa-users"></i> Browse Authors
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = subscriptions.map(sub => `
            <div class="subscription-card">
                <div class="author-info">
                    <div class="author-avatar">
                        ${sub.author_name.charAt(0)}
                    </div>
                    <div class="author-details">
                        <h3>${sub.author_name}</h3>
                        <p>${sub.author_bio || 'No bio available'}</p>
                        <div class="subscription-meta">
                            <span><i class="fas fa-book"></i> ${sub.book_count || 0} books</span>
                            <span><i class="fas fa-calendar"></i> Subscribed ${new Date(sub.created_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>
                <button class="btn btn-danger" onclick="app.unsubscribe(${sub.author_id})">
                    <i class="fas fa-heart-broken"></i> Unsubscribe
                </button>
            </div>
        `).join('');
    }

    async unsubscribe(authorId) {
        if (!confirm('Are you sure you want to unsubscribe from this author?')) {
            return;
        }

        try {
            await this.apiCall(`/subscriptions/${authorId}`, { method: 'DELETE' });
            this.showAlert('Unsubscribed successfully', 'success');
            this.loadSubscriptions(); // Refresh the list
        } catch (error) {
            this.showAlert(error.message, 'error');
        }
    }

    async loadAnalytics() {
        try {
            const response = await this.apiCall('/search/stats');
            this.displayAnalytics(response);
        } catch (error) {
            console.error('Failed to load analytics:', error);
            this.showAlert('Failed to load analytics', 'error');
        }
    }

    displayAnalytics(stats) {
        document.getElementById('totalSearches').textContent = stats.total_searches || 0;
        document.getElementById('totalQuestions').textContent = stats.total_rag_queries || 0;
        document.getElementById('totalTokens').textContent = (stats.total_tokens || 0).toLocaleString();
        document.getElementById('totalCost').textContent = `$${(stats.total_cost || 0).toFixed(4)}`;
    }

    async loadMyBooks() {
        try {
            const response = await this.apiCall('/books/');
            this.displayMyBooks(response);
        } catch (error) {
            console.error('Failed to load books:', error);
            this.showAlert('Failed to load your books', 'error');
        }
    }

    displayMyBooks(books) {
        const container = document.getElementById('myBooksList');
        
        if (!books || books.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-book" style="font-size: 3rem; color: var(--text-secondary); margin-bottom: 1rem;"></i>
                    <h3>No Books Uploaded</h3>
                    <p>You haven't uploaded any books yet. Upload your first book to share with your subscribers.</p>
                    <button class="btn btn-primary" onclick="app.switchTab('upload')">
                        <i class="fas fa-upload"></i> Upload Book
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = books.map(book => `
            <div class="book-card">
                <div class="book-info">
                    <h3>${book.title}</h3>
                    <p>${book.description || 'No description available'}</p>
                    <div class="book-meta">
                        <span><i class="fas fa-calendar"></i> ${new Date(book.created_at).toLocaleDateString()}</span>
                        <span class="status status-${book.processing_status}">
                            <i class="fas fa-${book.processing_status === 'completed' ? 'check' : book.processing_status === 'processing' ? 'spinner fa-spin' : 'exclamation-triangle'}"></i>
                            ${book.processing_status}
                        </span>
                    </div>
                </div>
                <div class="book-actions">
                    ${book.processing_status === 'completed' ? `
                        <button class="btn btn-secondary" onclick="app.viewBook(${book.id})">
                            <i class="fas fa-eye"></i> View
                        </button>
                    ` : ''}
                    <button class="btn btn-danger" onclick="app.deleteBook(${book.id})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');
    }

    async deleteBook(bookId) {
        if (!confirm('Are you sure you want to delete this book? This action cannot be undone.')) {
            return;
        }

        try {
            await this.apiCall(`/books/${bookId}`, { method: 'DELETE' });
            this.showAlert('Book deleted successfully', 'success');
            this.loadMyBooks(); // Refresh the list
        } catch (error) {
            this.showAlert(error.message, 'error');
        }
    }

    updateUserInfo() {
        if (this.currentUser) {
            // Update sidebar user info
            document.getElementById('sidebarUserName').textContent = this.currentUser.username || 'User';
            document.getElementById('sidebarUserRole').textContent = this.currentUser.role || 'user';
            
            // Update header user info
            document.getElementById('headerUserName').textContent = this.currentUser.username || 'User';
            
            // Show/hide author sections based on role
            const authorSection = document.getElementById('authorSection');
            if (this.currentUser.role === 'author') {
                authorSection.style.display = 'block';
            } else {
                authorSection.style.display = 'none';
            }
        }
    }

    showAuth() {
        console.log('=== showAuth called ===');
        const authSection = document.getElementById('authSection');
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.querySelector('.main-content');
        const sidebarBackdrop = document.getElementById('sidebarBackdrop');
        
        console.log('Elements found:', {
            authSection: !!authSection,
            sidebar: !!sidebar,
            mainContent: !!mainContent,
            sidebarBackdrop: !!sidebarBackdrop
        });
        
        // Hide dashboard elements first
        if (sidebar) {
            sidebar.classList.add('hidden');
            sidebar.classList.remove('active');
            sidebar.style.display = 'none';
            console.log('✓ Sidebar hidden');
        }
        if (mainContent) {
            mainContent.style.display = 'none';
            mainContent.classList.remove('sidebar-open');
            console.log('✓ Main content hidden');
        }
        if (sidebarBackdrop) {
            sidebarBackdrop.classList.remove('active');
            sidebarBackdrop.style.display = 'none';
            console.log('✓ Backdrop hidden');
        }
        
        // Show auth section
        if (authSection) {
            authSection.classList.remove('hidden');
            authSection.style.display = 'flex';
            authSection.style.visibility = 'visible';
            authSection.style.opacity = '1';
            authSection.style.position = 'absolute';
            authSection.style.top = '0';
            authSection.style.left = '0';
            authSection.style.width = '100vw';
            authSection.style.height = '100vh';
            authSection.style.zIndex = '2000';
            
            console.log('✓ Auth section shown');
            console.log('Auth section styles:', {
                display: authSection.style.display,
                visibility: authSection.style.visibility,
                opacity: authSection.style.opacity,
                position: authSection.style.position,
                zIndex: authSection.style.zIndex
            });
            
            // Force a reflow
            authSection.offsetHeight;
            
            console.log('Auth section computed display:', window.getComputedStyle(authSection).display);
            console.log('Auth section computed visibility:', window.getComputedStyle(authSection).visibility);
        } else {
            console.error('❌ Auth section not found!');
        }
        
        console.log('=== showAuth completed ===');
    }

    showDashboard() {
        console.log('showDashboard called');
        const authSection = document.getElementById('authSection');
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.querySelector('.main-content');
        
        console.log('Auth section:', authSection);
        console.log('Sidebar:', sidebar);
        console.log('Main content:', mainContent);
        
        // First, ensure auth is hidden
        if (authSection) {
            authSection.classList.add('hidden');
            authSection.style.display = 'none';
            console.log('Auth section hidden');
        }
        
        // Then show dashboard elements
        if (sidebar) {
            sidebar.classList.remove('hidden');
            sidebar.style.display = 'flex';
            console.log('Sidebar shown');
        }
        if (mainContent) {
            mainContent.style.display = 'flex';
            console.log('Main content shown');
        }
        
        this.updateUserInfo();
        
        // Setup sidebar navigation AFTER showing the dashboard
        this.setupSidebarNavigation();
        
        // Setup logout buttons
        const sidebarLogoutBtn = document.getElementById('sidebarLogoutBtn');
        const headerLogoutBtn = document.getElementById('headerLogoutBtn');
        
        if (sidebarLogoutBtn) {
            sidebarLogoutBtn.addEventListener('click', () => {
                console.log('Sidebar logout clicked');
                this.logout();
            });
        }
        
        if (headerLogoutBtn) {
            headerLogoutBtn.addEventListener('click', () => {
                console.log('Header logout clicked');
                this.logout();
            });
        }
        
        // Default to search tab for users, upload for authors
        const defaultTab = this.currentUser?.role === 'author' ? 'upload' : 'search';
        this.switchTab(defaultTab);
    }

    async checkMicrophonePermission() {
        try {
            if (navigator.permissions) {
                const permission = await navigator.permissions.query({ name: 'microphone' });
                console.log('🎤 Initial microphone permission:', permission.state);
                
                const voiceBtn = document.getElementById('voiceInputBtn');
                if (permission.state === 'denied' && voiceBtn) {
                    voiceBtn.classList.add('permission-needed');
                    voiceBtn.title = 'Microphone access denied. Click to see instructions.';
                }
                
                // Listen for permission changes
                permission.onchange = () => {
                    console.log('🎤 Microphone permission changed:', permission.state);
                    if (permission.state === 'granted' && voiceBtn) {
                        voiceBtn.classList.remove('permission-needed');
                        voiceBtn.title = 'Click to speak your question (auto-submits after 3 seconds of silence)';
                    }
                };
            }
        } catch (error) {
            console.log('🎤 Could not check microphone permission:', error);
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

        // Voice controls
        this.setupVoiceControls();

        // File upload drag & drop
        this.setupFileUpload();

        // Logout
        document.getElementById('logoutBtn')?.addEventListener('click', () => this.logout());
        
        console.log('Event listeners setup complete');
    }

    setupVoiceControls() {
        // Check for browser support
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Speech recognition not supported in this browser');
            const voiceBtn = document.getElementById('voiceInputBtn');
            if (voiceBtn) {
                voiceBtn.style.display = 'none';
            }
            return;
        }

        // Initialize speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        // Voice input button
        const voiceBtn = document.getElementById('voiceInputBtn');
        const voiceStatus = document.getElementById('voiceStatus');
        const ragQuery = document.getElementById('ragQuery');
        const voiceContainer = document.querySelector('.voice-input-container');

        voiceBtn?.addEventListener('click', () => {
            if (this.isListening) {
                this.stopListening();
            } else {
                this.requestMicrophonePermission();
            }
        });

        // Speech recognition events
        this.recognition.onstart = () => {
            console.log('🎤 Voice recognition started');
            this.isListening = true;
            voiceBtn?.classList.add('recording');
            voiceBtn?.classList.remove('permission-needed'); // Clear permission indicator
            voiceStatus?.classList.remove('hidden');
            voiceContainer?.classList.add('listening');
        };

        this.recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }

            // Update textarea with transcript
            if (finalTranscript) {
                ragQuery.value = finalTranscript.trim();
                console.log('🎤 Final transcript:', finalTranscript);
                
                // Reset the auto-submit timer
                this.resetSpeechTimeout();
            } else if (interimTranscript) {
                ragQuery.value = interimTranscript.trim();
                console.log('🎤 Interim transcript:', interimTranscript);
                
                // Set auto-submit timer for 3 seconds of silence
                this.resetSpeechTimeout();
            }
        };

        this.recognition.onend = () => {
            console.log('🎤 Voice recognition ended');
            this.isListening = false;
            voiceBtn?.classList.remove('recording');
            voiceStatus?.classList.add('hidden');
            voiceContainer?.classList.remove('listening');
        };

        this.recognition.onerror = (event) => {
            console.error('🎤 Voice recognition error:', event.error);
            this.stopListening();
            this.handleVoiceError(event.error);
        };

        // Stop speech button
        const stopSpeechBtn = document.getElementById('stopSpeechBtn');
        stopSpeechBtn?.addEventListener('click', () => {
            this.stopSpeaking();
        });
    }

    async requestMicrophonePermission() {
        try {
            // Check if we already have permission
            if (navigator.permissions) {
                const permission = await navigator.permissions.query({ name: 'microphone' });
                console.log('🎤 Microphone permission status:', permission.state);
                
                if (permission.state === 'denied') {
                    this.showMicrophonePermissionDialog();
                    return;
                }
            }

            // Try to start listening
            this.startListening();
            
        } catch (error) {
            console.error('🎤 Error checking microphone permission:', error);
            this.startListening(); // Fallback: try anyway
        }
    }

    handleVoiceError(error) {
        let message = '';
        let showDialog = false;

        switch (error) {
            case 'not-allowed':
                message = 'Microphone access denied. Please allow microphone access to use voice input.';
                showDialog = true;
                // Add visual indicator to microphone button
                const voiceBtn = document.getElementById('voiceInputBtn');
                if (voiceBtn) {
                    voiceBtn.classList.add('permission-needed');
                    voiceBtn.title = 'Click to enable microphone access';
                }
                break;
            case 'no-speech':
                message = 'No speech detected. Please try speaking again.';
                break;
            case 'audio-capture':
                message = 'No microphone found. Please check your microphone connection.';
                break;
            case 'network':
                message = 'Network error occurred. Please check your internet connection.';
                break;
            case 'service-not-allowed':
                message = 'Speech recognition service not allowed. Please try again.';
                break;
            case 'bad-grammar':
                message = 'Speech recognition grammar error. Please try again.';
                break;
            default:
                message = `Voice recognition error: ${error}. Please try again.`;
        }

        if (showDialog) {
            this.showMicrophonePermissionDialog();
        } else {
            this.showAlert(message, 'error');
        }
    }

    showMicrophonePermissionDialog() {
        const dialogHtml = `
            <div class="permission-dialog">
                <div class="permission-content">
                    <h3><i class="fas fa-microphone-slash"></i> Microphone Access Required</h3>
                    <p>To use voice input, please allow microphone access:</p>
                    <ol>
                        <li>Click the microphone icon in your browser's address bar</li>
                        <li>Select "Allow" for microphone access</li>
                        <li>Refresh the page if needed</li>
                        <li>Try the voice input again</li>
                    </ol>
                    <div class="browser-instructions">
                        <strong>Chrome/Edge:</strong> Look for <i class="fas fa-microphone"></i> in the address bar<br>
                        <strong>Firefox:</strong> Look for <i class="fas fa-microphone"></i> in the address bar<br>
                        <strong>Safari:</strong> Check Safari → Settings → Websites → Microphone
                    </div>
                    <div class="permission-actions">
                        <button onclick="this.closest('.permission-dialog').remove()" class="btn btn-primary">
                            Got it!
                        </button>
                        <button onclick="window.location.reload()" class="btn btn-secondary">
                            Refresh Page
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Remove any existing dialog
        const existingDialog = document.querySelector('.permission-dialog');
        if (existingDialog) {
            existingDialog.remove();
        }

        // Add new dialog
        document.body.insertAdjacentHTML('beforeend', dialogHtml);
    }

    startListening() {
        if (!this.recognition) return;
        
        try {
            console.log('🎤 Starting voice input...');
            this.recognition.start();
            
            // Clear any existing text
            const ragQuery = document.getElementById('ragQuery');
            if (ragQuery) {
                ragQuery.value = '';
            }
        } catch (error) {
            console.error('🎤 Error starting voice recognition:', error);
            this.showAlert('Failed to start voice input', 'error');
        }
    }

    stopListening() {
        if (!this.recognition || !this.isListening) return;
        
        console.log('🎤 Stopping voice input...');
        this.recognition.stop();
        this.clearSpeechTimeout();
    }

    resetSpeechTimeout() {
        this.clearSpeechTimeout();
        
        // Auto-submit after 3 seconds of silence
        this.speechTimeout = setTimeout(() => {
            console.log('🎤 Auto-submitting after 3 seconds of silence');
            const ragQuery = document.getElementById('ragQuery');
            if (ragQuery && ragQuery.value.trim()) {
                this.stopListening();
                // Trigger form submission
                const ragForm = document.getElementById('ragForm');
                if (ragForm) {
                    const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
                    ragForm.dispatchEvent(submitEvent);
                }
            }
        }, 3000);
    }

    clearSpeechTimeout() {
        if (this.speechTimeout) {
            clearTimeout(this.speechTimeout);
            this.speechTimeout = null;
        }
    }

    // Speak text while streaming is still happening
    speakStreamingText() {
        const answerDiv = document.getElementById('streaming-answer');
        if (!answerDiv || this.isSpeaking || !this.speechSynthesis || this.userStoppedSpeech) return;
        
        const textToSpeak = answerDiv.textContent || '';
        if (!textToSpeak.trim() || textToSpeak.length < 50) return;
        
        console.log('🔊 Speaking streaming text:', textToSpeak.substring(0, 50) + '...');
        
        // Create utterance
        this.currentUtterance = new SpeechSynthesisUtterance(textToSpeak);
        this.currentUtterance.rate = 0.9;
        this.currentUtterance.pitch = 1.0;
        this.currentUtterance.volume = 0.8;
        
        // Show speech controls
        const speechControls = document.getElementById('speechControls');
        speechControls?.classList.remove('hidden');
        this.isSpeaking = true;
        
        this.currentUtterance.onstart = () => {
            console.log('🔊 TTS started during streaming');
        };
        
        this.currentUtterance.onend = () => {
            console.log('🔊 TTS segment ended');
            this.isSpeaking = false;
            
            // Don't continue if user stopped speech
            if (this.userStoppedSpeech) {
                console.log('🔊 User stopped speech, not continuing');
                speechControls?.classList.add('hidden');
                return;
            }
            
            // Check if streaming is still happening and there's more content
            const currentText = answerDiv.textContent || '';
            const isStreamingComplete = answerDiv.classList.contains('complete');
            
            if (!isStreamingComplete && currentText.length > textToSpeak.length + 100) {
                // More content has arrived, speak the new content
                console.log('🔊 More content available, continuing speech');
                this.ttsTimeout = setTimeout(() => {
                    if (!this.isSpeaking && !this.userStoppedSpeech) {
                        this.speakStreamingText();
                    }
                }, 500); // Short delay before continuing
            } else if (isStreamingComplete && currentText.length > textToSpeak.length) {
                // Streaming finished while we were speaking, speak the rest
                console.log('🔊 Streaming complete, speaking remaining content');
                this.ttsTimeout = setTimeout(() => {
                    if (!this.isSpeaking && !this.userStoppedSpeech) {
                        this.speakDisplayedText();
                    }
                }, 500);
            } else {
                // No more content or streaming not complete yet
                console.log('🔊 Waiting for more content or completion');
                speechControls?.classList.add('hidden');
            }
        };
        
        this.currentUtterance.onerror = (event) => {
            console.error('🔊 TTS error during streaming:', event.error);
            this.isSpeaking = false;
            
            // Only hide controls on non-interrupted errors
            if (event.error !== 'interrupted') {
                speechControls?.classList.add('hidden');
            }
            
            // Don't retry if user stopped speech or if it's a non-recoverable error
            if (this.userStoppedSpeech || event.error === 'not-allowed' || event.error === 'network') {
                console.log('🔊 Not retrying due to user action or non-recoverable error');
                return;
            }
        };
        
        // Speak the text
        this.speechSynthesis.speak(this.currentUtterance);
    }

    // Simple TTS that reads displayed text
    handleStreamingTTS() {
        if (!this.speechSynthesis || this.isSpeaking) return;
        
        const answerDiv = document.getElementById('streaming-answer');
        if (!answerDiv) return;
        
        // Only speak if streaming is complete to avoid interruptions
        if (answerDiv.classList.contains('complete')) {
            const displayedText = answerDiv.textContent || '';
            if (displayedText.length > 50) {
                console.log('🔊 Starting TTS for complete answer');
                this.speakDisplayedText();
            }
        }
    }

    speakDisplayedText() {
        const answerDiv = document.getElementById('streaming-answer');
        if (!answerDiv || this.isSpeaking || this.userStoppedSpeech) return;
        
        const textToSpeak = answerDiv.textContent || '';
        if (!textToSpeak.trim()) return;
        
        console.log('🔊 Speaking displayed text:', textToSpeak.substring(0, 50) + '...');
        
        // Create utterance
        this.currentUtterance = new SpeechSynthesisUtterance(textToSpeak);
        this.currentUtterance.rate = 0.9;
        this.currentUtterance.pitch = 1.0;
        this.currentUtterance.volume = 0.8;
        
        // Show speech controls
        const speechControls = document.getElementById('speechControls');
        speechControls?.classList.remove('hidden');
        this.isSpeaking = true;
        
        this.currentUtterance.onstart = () => {
            console.log('🔊 TTS started');
        };
        
        this.currentUtterance.onend = () => {
            console.log('🔊 TTS ended naturally');
            this.isSpeaking = false;
            
            // Don't continue if user stopped speech
            if (this.userStoppedSpeech) {
                console.log('🔊 User stopped speech, session complete');
                speechControls?.classList.add('hidden');
                return;
            }
            
            // Check if there's significantly more content to speak (only if streaming is still active)
            const currentText = answerDiv.textContent || '';
            const isStreamingComplete = answerDiv.classList.contains('complete');
            
            if (!isStreamingComplete && currentText.length > textToSpeak.length + 100) {
                // Wait a bit then speak the new content
                console.log('🔊 More content available, will speak again');
                this.ttsTimeout = setTimeout(() => {
                    if (!this.isSpeaking && !this.userStoppedSpeech) {
                        this.speakDisplayedText();
                    }
                }, 1500); // Longer delay to avoid interruptions
            } else {
                // Hide controls if done or no significant new content
                console.log('🔊 Speech session complete');
                speechControls?.classList.add('hidden');
            }
        };
        
        this.currentUtterance.onerror = (event) => {
            console.error('🔊 TTS error:', event.error);
            this.isSpeaking = false;
            
            // Don't hide controls immediately on interruption - might be temporary
            if (event.error !== 'interrupted') {
                const speechControls = document.getElementById('speechControls');
                speechControls?.classList.add('hidden');
            }
            
            // Don't retry if user stopped speech or if it's a non-recoverable error
            if (this.userStoppedSpeech || event.error === 'not-allowed' || event.error === 'network') {
                console.log('🔊 Not retrying due to user action or non-recoverable error');
                return;
            }
        };
        
        // Speak the text
        this.speechSynthesis.speak(this.currentUtterance);
    }

    stopSpeaking() {
        console.log('🔊 Stopping speech - user requested or cleanup');
        
        // Cancel any ongoing speech
        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }
        
        // Clear all timeouts
        clearTimeout(this.ttsTimeout);
        
        // Reset all flags
        this.isSpeaking = false;
        this.ttsStarted = false;
        this.userStoppedSpeech = true; // Flag to prevent auto-restart
        
        // Hide controls
        const speechControls = document.getElementById('speechControls');
        speechControls?.classList.add('hidden');
        
        // Clear current utterance
        this.currentUtterance = null;
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


    async loadUserData() {
        try {
            // Load user data from localStorage
            const userRole = localStorage.getItem('userRole');
            const userId = localStorage.getItem('userId');
            const username = localStorage.getItem('username');
            const email = localStorage.getItem('email');
            
            console.log('Loading user data from localStorage:', {
                userRole,
                userId,
                username,
                email
            });
            
            if (userRole && userId && username && email) {
                this.currentUser = {
                    id: parseInt(userId),
                    role: userRole,
                    username: username,
                    email: email
                };
                console.log('User data loaded successfully:', this.currentUser);
            } else {
                console.log('Incomplete user data in localStorage');
                throw new Error('Incomplete user data');
            }
        } catch (error) {
            console.error('Failed to load user data:', error);
            throw error;
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            this.showLoading('Signing in...');
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
                role: response.user_role,
                username: formData.get('email').split('@')[0], // Extract username from email
                email: formData.get('email')
            };
            localStorage.setItem('userRole', response.user_role);
            localStorage.setItem('userId', response.user_id);
            localStorage.setItem('username', this.currentUser.username);
            localStorage.setItem('email', this.currentUser.email);
            
            this.showDashboard();
            this.showAlert('Welcome back!', 'success');
        } catch (error) {
            this.showAlert(error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    async handleRegister(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        
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
                role: response.user_role,
                username: formData.get('username'),
                email: formData.get('email')
            };
            localStorage.setItem('userRole', response.user_role);
            localStorage.setItem('userId', response.user_id);
            localStorage.setItem('username', this.currentUser.username);
            localStorage.setItem('email', this.currentUser.email);
            
            this.showDashboard();
            this.showAlert('Account created successfully! Welcome to BookRAG Pro!', 'success');
        } catch (error) {
            console.error('Registration error:', error);
            this.showAlert(error.message, 'error');
        } finally {
            this.hideLoading();
        }
    }

    logout() {
        console.log('Logout called');
        
        // Clean up voice functionality
        this.stopListening();
        this.stopSpeaking();
        this.clearSpeechTimeout();
        
        // Clear all auth data
        this.clearAuthData();
        
        console.log('Calling showAuth from logout');
        this.showAuth();
        
        // Show alert after a small delay to ensure auth is visible
        setTimeout(() => {
            this.showAlert('Logged out successfully', 'info');
        }, 100);
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
        
        // Start timing
        const searchStartTime = performance.now();
        console.log(`🔍 FRONTEND SEARCH START: "${query}"`);
        
        try {
            this.showLoading('Searching...');
            
            // Time the API call
            const apiStartTime = performance.now();
            const response = await this.apiCall('/search/semantic', {
                method: 'POST',
                body: JSON.stringify({
                    query: query,
                    limit: 10
                })
            });
            const apiEndTime = performance.now();
            const apiTime = apiEndTime - apiStartTime;
            
            console.log(`🌐 API Call Time: ${apiTime.toFixed(1)}ms`);
            
            // Time the result display
            const displayStartTime = performance.now();
            this.displaySearchResults(response.results, query);
            const displayEndTime = performance.now();
            const displayTime = displayEndTime - displayStartTime;
            
            console.log(`🎨 Display Time: ${displayTime.toFixed(1)}ms`);
            
            // Calculate total time
            const totalTime = performance.now() - searchStartTime;
            console.log(`✅ FRONTEND SEARCH COMPLETE: ${totalTime.toFixed(1)}ms total`);
            console.log(`   - API: ${apiTime.toFixed(1)}ms (${((apiTime/totalTime)*100).toFixed(1)}%)`);
            console.log(`   - Display: ${displayTime.toFixed(1)}ms (${((displayTime/totalTime)*100).toFixed(1)}%)`);
            
            // Show performance info to user if search is slow
            if (totalTime > 3000) {
                console.warn(`⚠️ Slow search detected: ${totalTime.toFixed(1)}ms`);
            }
            
        } catch (error) {
            const errorTime = performance.now() - searchStartTime;
            console.error(`❌ SEARCH ERROR after ${errorTime.toFixed(1)}ms:`, error.message);
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
            // Use streaming endpoint for faster response
            await this.handleRAGQueryStream(query);
            
        } catch (error) {
            this.showAlert(error.message, 'error');
        }
        // Don't hide loading here - let streaming handle it
    }

    async handleRAGQueryStream(query) {
        const container = document.getElementById('ragResults');
        
        // Stop any current speech and clear timeouts
        this.stopSpeaking();
        clearTimeout(this.ttsTimeout);
        this.ttsStarted = false; // Reset TTS flag for new query
        this.userStoppedSpeech = false; // Reset user stop flag for new query
        
        // Show initial loading
        this.showLoading('Finding relevant sources...');
        
        // Clear previous results and show loading state
        container.innerHTML = `
            <div class="rag-container">
                <h3>Answer for: "${query}"</h3>
                <div class="answer-section">
                    <h4><i class="fas fa-robot"></i> AI Answer</h4>
                    <div id="answer-container" class="loading">
                        <i class="fas fa-spinner fa-spin"></i> Searching for relevant content...
                    </div>
                </div>
                <div class="sources-section">
                    <h4><i class="fas fa-book"></i> Sources</h4>
                    <div id="sources-container" class="loading">
                        <i class="fas fa-spinner fa-spin"></i> Preparing sources...
                    </div>
                </div>
            </div>
        `;

        try {
            const token = localStorage.getItem('token');
            console.log('🚀 Starting RAG stream request...');
            
            const response = await fetch('/api/v1/search/rag-stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    query: query,
                    max_chunks: 10  // Updated to use 10 chunks
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('🚀 HTTP Error:', response.status, errorText);
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }

            console.log('🚀 Response received, starting to read stream...');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let answerText = '';
            let buffer = ''; // Buffer for incomplete lines

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log('🚀 Stream reading complete');
                    break;
                }

                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;
                
                // Process complete lines
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep incomplete line in buffer
                
                console.log('🚀 Processing', lines.length, 'lines from chunk');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonStr = line.slice(6).trim();
                            if (jsonStr) {
                                console.log('🚀 Parsing JSON:', jsonStr.substring(0, 100) + '...');
                                const data = JSON.parse(jsonStr);
                                console.log('🚀 Parsed data type:', data.type);
                                
                                if (data.type === 'sources') {
                                    console.log('🚀 Received sources:', data.sources?.length || 0);
                                    // Hide fullscreen loader once sources arrive
                                    this.hideLoading();
                                    
                                    if (data.sources && data.sources.length > 0) {
                                        this.displayStreamingSources(data.sources);
                                    } else {
                                        console.warn('🚀 No sources in data');
                                        const sourcesContainer = document.getElementById('sources-container');
                                        if (sourcesContainer) {
                                            sourcesContainer.innerHTML = '<p>No sources found for this query.</p>';
                                        }
                                    }
                                } else if (data.type === 'answer_chunk') {
                                    console.log('🚀 Adding answer chunk, length:', data.content?.length || 0);
                                    answerText += data.content || '';
                                    this.updateStreamingAnswer(answerText);
                                } else if (data.type === 'complete') {
                                    console.log(`✅ RAG Stream Complete: ${data.total_time?.toFixed(3) || 'unknown'}s`);
                                    this.finalizeStreamingAnswer();
                                } else if (data.type === 'error') {
                                    console.error('🚀 Stream error from server:', data.message);
                                    // Hide loader and show error properly
                                    this.hideLoading();
                                    this.showNoContentError(data.message);
                                    return; // Exit the stream processing
                                } else {
                                    console.log('🚀 Unknown data type:', data.type);
                                }
                            }
                        } catch (parseError) {
                            console.error('❌ Failed to parse streaming data:', parseError);
                            console.error('❌ Problematic line:', line);
                        }
                    } else if (line.trim()) {
                        console.log('🚀 Non-data line:', line);
                    }
                }
            }
            
            // Process any remaining buffer
            if (buffer.trim()) {
                console.log('🚀 Processing remaining buffer:', buffer);
            }
            
        } catch (error) {
            console.error('❌ Streaming error:', error);
            this.hideLoading(); // Ensure loader is always hidden
            
            // Show detailed error information
            container.innerHTML = `
                <div class="rag-container">
                    <div class="no-content-error">
                        <div class="error-icon">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <h3>Something Went Wrong</h3>
                        <p class="error-message">Failed to generate answer: ${error.message}</p>
                        <div class="suggestions">
                            <h4>What you can try:</h4>
                            <ul>
                                <li><i class="fas fa-redo"></i> Try asking your question again</li>
                                <li><i class="fas fa-wifi"></i> Check your internet connection</li>
                                <li><i class="fas fa-users"></i> Make sure you're subscribed to authors</li>
                                <li><i class="fas fa-refresh"></i> Refresh the page if the problem persists</li>
                            </ul>
                        </div>
                        <div class="error-actions">
                            <button onclick="document.getElementById('ragQuery').focus()" class="btn btn-primary">
                                <i class="fas fa-edit"></i> Try Again
                            </button>
                            <button onclick="window.location.reload()" class="btn btn-secondary">
                                <i class="fas fa-refresh"></i> Refresh Page
                            </button>
                        </div>
                        <details style="margin-top: 1rem;">
                            <summary style="cursor: pointer; color: #6c757d;">Technical Details</summary>
                            <pre style="background: #f8f9fa; padding: 1rem; margin-top: 0.5rem; border-radius: 4px; overflow-x: auto; text-align: left;">${error.stack || error.toString()}</pre>
                        </details>
                    </div>
                </div>
            `;
        }
    }

    displayStreamingSources(sources) {
        const sourcesContainer = document.getElementById('sources-container');
        
        if (!sources || sources.length === 0) {
            sourcesContainer.innerHTML = '<p>No sources found.</p>';
            return;
        }

        sourcesContainer.innerHTML = sources.map((source, index) => `
            <div class="source-item clickable-source" 
                 data-book-id="${source.book_id}" 
                 data-section-title="${source.section_title.replace(/"/g, '&quot;')}" 
                 data-page-number="${source.page_number}" 
                 data-text="${encodeURIComponent(source.text)}"
                 style="cursor: pointer;">
                <div class="source-header">
                    <span class="source-number">${index + 1}</span>
                    <span class="source-title">${source.section_title}</span>
                    <span class="source-page">Page ${source.page_number}</span>
                    <span class="source-score">${(source.score * 100).toFixed(1)}%</span>
                </div>
                <div class="source-text">${this.truncateToFirstSentence(source.text)}</div>
                <div class="source-actions">
                    <i class="fas fa-external-link-alt"></i> Click to view in PDF
                </div>
            </div>
        `).join('');

        // Add click handlers to make sources clickable
        const clickableSources = sourcesContainer.querySelectorAll('.clickable-source');
        console.log(`🔍 Adding click handlers to ${clickableSources.length} sources`);
        
        clickableSources.forEach((sourceElement, index) => {
            console.log(`🔍 Adding click handler to source ${index + 1}:`, sourceElement.dataset);
            
            sourceElement.addEventListener('click', (e) => {
                console.log(`🔍 Source ${index + 1} clicked!`);
                this.handleStreamingSourceClick(e, sourceElement);
            });
            
            // Also add visual feedback
            sourceElement.style.cursor = 'pointer';
        });

        // Enable answer section
        const answerContainer = document.getElementById('answer-container');
        answerContainer.innerHTML = '<div id="streaming-answer">Generating answer...</div>';
        answerContainer.classList.remove('loading');
        
        console.log('🚀 Sources displayed, answer section ready for streaming');
    }

    handleStreamingSourceClick(e, sourceElement) {
        e.preventDefault();
        e.stopPropagation();
        
        try {
            console.log('🔍 Streaming source clicked - element:', sourceElement);
            console.log('🔍 Dataset:', sourceElement.dataset);
            
            // Extract data from the clicked source
            const bookId = parseInt(sourceElement.dataset.bookId);
            const sectionTitle = sourceElement.dataset.sectionTitle;
            const pageNumber = parseInt(sourceElement.dataset.pageNumber);
            const encodedText = sourceElement.dataset.text;
            
            console.log('🔍 Extracted data:');
            console.log('  Book ID:', bookId, typeof bookId);
            console.log('  Section:', sectionTitle, typeof sectionTitle);
            console.log('  Page:', pageNumber, typeof pageNumber);
            console.log('  Text length:', encodedText ? encodedText.length : 0);
            
            // Validate required data
            if (!bookId || !sectionTitle) {
                throw new Error('Missing required data: bookId or sectionTitle');
            }
            
            // Decode the text for highlighting
            const textToHighlight = encodedText ? decodeURIComponent(encodedText) : '';
            console.log('🔍 Text to highlight preview:', textToHighlight.substring(0, 100));
            
            // Check if openPdfViewer function exists
            if (typeof window.openPdfViewer !== 'function') {
                throw new Error('openPdfViewer function not found');
            }
            
            // Call the same PDF viewer function as regular search results
            console.log('🔍 Calling openPdfViewer...');
            window.openPdfViewer(bookId, sectionTitle, pageNumber, textToHighlight);
            
        } catch (error) {
            console.error('❌ Error in handleStreamingSourceClick:', error);
            console.error('❌ Error stack:', error.stack);
            this.showAlert(`Failed to open PDF viewer: ${error.message}`, 'error');
        }
    }

    updateStreamingAnswer(text) {
        const answerDiv = document.getElementById('streaming-answer');
        if (answerDiv) {
            console.log('🚀 Updating streaming answer, length:', text.length);
            
            // Convert markdown-like formatting to HTML
            const formattedText = text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>');
            
            answerDiv.innerHTML = `<p>${formattedText}</p>`;
            
            // Auto-scroll to bottom
            answerDiv.scrollTop = answerDiv.scrollHeight;
            
            // Add typing cursor effect
            if (!answerDiv.classList.contains('streaming')) {
                answerDiv.classList.add('streaming');
                console.log('🚀 Added streaming class to answer div');
            }

            // Start TTS after 1 second of streaming with substantial content
            if (!this.isSpeaking && !this.ttsStarted && text.length > 100) {
                console.log('🔊 Scheduling TTS to start in 1 second...');
                this.ttsStarted = true; // Mark that we've started TTS process
                setTimeout(() => {
                    if (!this.isSpeaking) {
                        console.log('🔊 Starting TTS during streaming');
                        this.speakStreamingText();
                    }
                }, 100); // Start speaking after 1 second
            }
        }
    }

    showNoContentError(message) {
        const container = document.getElementById('ragResults');
        container.innerHTML = `
            <div class="rag-container">
                <div class="no-content-error">
                    <div class="error-icon">
                        <i class="fas fa-search"></i>
                        <i class="fas fa-times-circle error-overlay"></i>
                    </div>
                    <h3>No Relevant Content Found</h3>
                    <p class="error-message">${message}</p>
                    <div class="suggestions">
                        <h4>Try these suggestions:</h4>
                        <ul>
                            <li><i class="fas fa-lightbulb"></i> Use different keywords or phrases</li>
                            <li><i class="fas fa-users"></i> Subscribe to more authors in the Authors tab</li>
                            <li><i class="fas fa-question-circle"></i> Ask more specific questions</li>
                            <li><i class="fas fa-book"></i> Check if the topic is covered in your subscribed books</li>
                        </ul>
                    </div>
                    <div class="error-actions">
                        <button onclick="document.getElementById('ragQuery').focus()" class="btn btn-primary">
                            <i class="fas fa-edit"></i> Try Another Question
                        </button>
                        <button onclick="app.switchTab('authors')" class="btn btn-secondary">
                            <i class="fas fa-users"></i> Browse Authors
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    finalizeStreamingAnswer() {
        const answerContainer = document.getElementById('answer-container');
        const answerDiv = document.getElementById('streaming-answer');
        
        if (answerContainer) {
            answerContainer.classList.add('complete');
        }
        
        if (answerDiv) {
            answerDiv.classList.remove('streaming');
            answerDiv.classList.add('complete');
            
            // Clear any pending TTS timeout
            clearTimeout(this.ttsTimeout);
            
            // If TTS is already running, let it continue and handle the completion
            // If not running, start speaking the complete answer
            if (!this.isSpeaking && answerDiv.textContent.trim()) {
                console.log('🔊 Speaking complete answer after streaming finished');
                setTimeout(() => {
                    this.speakDisplayedText();
                }, 500); // Small delay to ensure DOM is updated
            } else if (this.isSpeaking) {
                console.log('🔊 TTS already running, will continue with remaining content');
                // The ongoing TTS will handle speaking the rest in its onend event
            }
        }
    }

    truncateToFirstSentence(text, maxLength = 150) {
        if (!text) return '';
        
        // Find the first sentence ending
        const sentenceEnders = /[.!?]/;
        const match = text.match(sentenceEnders);
        
        if (match) {
            const firstSentenceEnd = match.index + 1;
            const firstSentence = text.substring(0, firstSentenceEnd).trim();
            
            // If first sentence is reasonable length, use it
            if (firstSentence.length <= maxLength) {
                return firstSentence + '...';
            }
        }
        
        // Fallback: truncate at word boundary near maxLength
        if (text.length <= maxLength) {
            return text;
        }
        
        const truncated = text.substring(0, maxLength);
        const lastSpace = truncated.lastIndexOf(' ');
        
        if (lastSpace > maxLength * 0.7) { // If we can find a good word boundary
            return truncated.substring(0, lastSpace) + '...';
        }
        
        return truncated + '...';
    }

    // Keep the old method as fallback
    async handleRAGOld(e) {
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
                    <div class="result-text">${this.truncateToFirstSentence(result.text)}</div>
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
                                            "${this.truncateToFirstSentence(source.text)}"
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
    
    cleanup() {
        console.log('🧹 Cleaning up app resources');
        
        // Stop any ongoing speech
        this.stopSpeaking();
        
        // Stop listening
        this.stopListening();
        
        // Clear all timeouts
        clearTimeout(this.speechTimeout);
        clearTimeout(this.ttsTimeout);
        
        // Cancel any ongoing speech synthesis
        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }
        
        // Reset all flags
        this.isSpeaking = false;
        this.isListening = false;
        this.ttsStarted = false;
        this.userStoppedSpeech = false;
        
        // Clear current utterance
        this.currentUtterance = null;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing app...');
    console.log('Auth section exists:', !!document.getElementById('authSection'));
    console.log('Sidebar exists:', !!document.getElementById('sidebar'));
    console.log('Main content exists:', !!document.querySelector('.main-content'));
    
    try {
        window.app = new BookRAGApp();
        console.log('App initialized successfully:', window.app);
    } catch (error) {
        console.error('Failed to initialize app:', error);
        console.error('Error stack:', error.stack);
    }
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