class AdminApp {
    constructor() {
        this.apiBase = '/api/v1/admin';
        this.token = localStorage.getItem('token');
        this.currentUser = null;
        
        // PDF Viewer State
        this.pdfDoc = null;
        this.pageNum = 1;
        this.pageRendering = false;
        this.pageNumPending = null;
        this.scale = 1.0;
        this.canvas = null;
        this.ctx = null;

        this.init();
    }

    async init() {
        if (!this.token) {
            window.location.href = '/admin-login';
            return;
        }

        try {
            // Validate token and role
            const response = await fetch('/api/v1/users/profile', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            if (!response.ok) throw new Error('Unauthorized');
            
            const user = await response.json();
            if (user.role !== 'superadmin') {
                alert('Access denied. Superadmin only.');
                window.location.href = '/';
                return;
            }
            
            this.currentUser = user;
            this.setupEventListeners();
            this.loadUsers(); // Default tab
        } catch (error) {
            console.error('Init error:', error);
            localStorage.removeItem('token');
            window.location.href = '/admin-login';
        }
    }

    setupEventListeners() {
        // Sidebar navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = item.dataset.tab;
                this.switchTab(tab);
            });
        });

        // Settings form submission
        const settingsForm = document.getElementById('systemSettingsForm');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveSystemSettings();
            });
        }

        // Logout
        document.getElementById('adminLogoutBtn').addEventListener('click', () => {
            localStorage.removeItem('token');
            localStorage.removeItem('userRole');
            window.location.href = '/admin-login';
        });
    }

    switchTab(tabName) {
        // Update UI
        document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
        const navItem = document.querySelector(`[data-tab="${tabName}"]`);
        if (navItem) navItem.classList.add('active');

        document.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));
        
        // Handle sub-views
        if (tabName === 'authorDetails') {
            document.getElementById('authorDetailsView').classList.remove('hidden');
        } else if (tabName === 'readerDetails') {
            document.getElementById('readerDetailsView').classList.remove('hidden');
        } else {
            const tab = document.getElementById(`${tabName}Tab`);
            if (tab) tab.classList.remove('hidden');
        }

        // Update titles
        const titles = {
            'users': { title: 'User Management', subtitle: 'Manage all users and their roles' },
            'authors': { title: 'Author Management', subtitle: 'View all authors and their uploaded books' },
            'readers': { title: 'Reader Management', subtitle: 'View all readers and their activity' },
            'books': { title: 'Global Library', subtitle: 'View and manage all books in the system' },
            'stats': { title: 'Global Stats', subtitle: 'System-wide analytics and usage' },
            'usageLogs': { title: 'Advanced Usage Logs', subtitle: 'Detailed tracking and cost analysis' },
            'settings': { title: 'System Settings', subtitle: 'Configure platform-wide parameters' },
            'authorDetails': { title: 'Author Details', subtitle: 'Detailed view of author profile and books' },
            'readerDetails': { title: 'Reader Details', subtitle: 'Detailed view of reader profile and usage' }
        };
        
        const info = titles[tabName];
        if (info) {
            document.getElementById('pageTitle').textContent = info.title;
            document.getElementById('pageSubtitle').textContent = info.subtitle;
        }

        // Load data
        if (tabName === 'users') this.loadUsers();
        if (tabName === 'authors') this.loadAuthors();
        if (tabName === 'readers') this.loadReaders();
        if (tabName === 'books') this.loadGlobalBooks();
        if (tabName === 'stats') this.loadGlobalStats();
        if (tabName === 'usageLogs') this.loadAdvancedUsageStats();
        if (tabName === 'settings') this.loadSystemSettings();
    }

    async apiCall(endpoint, options = {}) {
        const url = `${this.apiBase}${endpoint}`;
        const headers = {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json',
            ...options.headers
        };

        const response = await fetch(url, { ...options, headers });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API call failed');
        }
        return response.json();
    }

    async loadUsers() {
        try {
            const users = await this.apiCall('/users');
            const tbody = document.getElementById('usersTableBody');
            tbody.innerHTML = users.map(user => `
                <tr>
                    <td><span class="user-id">#${user.id}</span></td>
                    <td>
                        <div class="user-info-cell">
                            <div class="user-avatar-small">${user.username.charAt(0).toUpperCase()}</div>
                            <span>${user.username}</span>
                        </div>
                    </td>
                    <td>${user.email}</td>
                    <td>
                        <select class="role-select" onchange="adminApp.updateUserRole(${user.id}, this.value)">
                            <option value="user" ${user.role === 'user' ? 'selected' : ''}>Reader</option>
                            <option value="author" ${user.role === 'author' ? 'selected' : ''}>Author</option>
                            <option value="superadmin" ${user.role === 'superadmin' ? 'selected' : ''}>Superadmin</option>
                        </select>
                    </td>
                    <td><span class="status status-${user.is_active ? 'active' : 'inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td>
                        <div class="action-btns">
                            <button class="btn btn-danger btn-sm" onclick="adminApp.deleteUser(${user.id})" title="Delete User">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            alert(error.message);
        }
    }

    async updateUserRole(userId, newRole) {
        try {
            await this.apiCall(`/users/${userId}/role?role=${newRole}`, { method: 'PUT' });
            alert('Role updated successfully');
        } catch (error) {
            alert(error.message);
        }
    }

    async deleteUser(userId) {
        if (!confirm('Are you sure you want to delete this user?')) return;
        try {
            await this.apiCall(`/users/${userId}`, { method: 'DELETE' });
            this.loadUsers();
        } catch (error) {
            alert(error.message);
        }
    }

    async loadGlobalBooks() {
        try {
            const books = await this.apiCall('/books/all');
            const container = document.getElementById('globalBooksList');
            container.innerHTML = books.map(book => `
                <div class="book-card">
                    <div class="book-info">
                        <h3>${book.title}</h3>
                        <p>Author: <strong>${book.author_name}</strong></p>
                    </div>
                    <div class="book-actions">
                        <span class="status status-${book.processing_status}">${book.processing_status}</span>
                        <button class="btn btn-primary btn-sm" onclick="adminApp.viewBookPdf(${book.id}, '${book.title.replace(/'/g, "\\'")}')">
                            <i class="fas fa-eye"></i> View PDF
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            alert(error.message);
        }
    }

    async loadGlobalStats() {
        try {
            const stats = await this.apiCall('/stats/global');
            const container = document.getElementById('globalStatsSummary');
            container.innerHTML = `
                <div class="analytics-card">
                    <div class="analytics-icon"><i class="fas fa-users"></i></div>
                    <div class="analytics-content">
                        <h3>${stats.total_users}</h3>
                        <p>Total Users</p>
                    </div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-icon"><i class="fas fa-pen-nib"></i></div>
                    <div class="analytics-content">
                        <h3>${stats.total_authors}</h3>
                        <p>Total Authors</p>
                    </div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-icon"><i class="fas fa-book"></i></div>
                    <div class="analytics-content">
                        <h3>${stats.total_books}</h3>
                        <p>Total Books</p>
                    </div>
                </div>
            `;
        } catch (error) {
            alert(error.message);
        }
    }

    async loadAuthors() {
        try {
            const authors = await this.apiCall('/authors');
            const tbody = document.getElementById('authorsTableBody');
            tbody.innerHTML = authors.map(author => `
                <tr>
                    <td><span class="user-id">#${author.id}</span></td>
                    <td>
                        <div class="user-info-cell">
                            <div class="user-avatar-small">${author.username.charAt(0).toUpperCase()}</div>
                            <span>${author.username}</span>
                        </div>
                    </td>
                    <td>${author.email}</td>
                    <td><span class="badge">Author</span></td>
                    <td>
                        <button class="btn btn-primary btn-sm" onclick="adminApp.viewAuthorDetails(${author.id})">
                            <i class="fas fa-eye"></i> View Details
                        </button>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            alert(error.message);
        }
    }

    async viewAuthorDetails(authorId) {
        try {
            const authors = await this.apiCall('/authors');
            const author = authors.find(a => a.id === authorId);
            if (!author) throw new Error('Author not found');

            const books = await this.apiCall(`/authors/${authorId}/books`);
            
            this.switchTab('authorDetails');
            document.getElementById('detailAuthorName').textContent = author.username;
            
            document.getElementById('authorInfoContent').innerHTML = `
                <div class="info-row"><strong>Email:</strong> ${author.email}</div>
                <div class="info-row"><strong>Username:</strong> ${author.username}</div>
                <div class="info-row"><strong>Joined:</strong> ${new Date(author.created_at).toLocaleDateString()}</div>
                <div class="info-row"><strong>Status:</strong> <span class="status status-${author.is_active ? 'active' : 'inactive'}">${author.is_active ? 'Active' : 'Inactive'}</span></div>
            `;

            const booksList = document.getElementById('authorBooksList');
            if (books.length === 0) {
                booksList.innerHTML = '<p class="no-data">No books uploaded yet.</p>';
            } else {
                booksList.innerHTML = books.map(book => `
                    <div class="book-item-mini">
                        <div class="book-icon"><i class="fas fa-file-pdf"></i></div>
                        <div class="book-info">
                            <h4>${book.title}</h4>
                            <span class="status status-${book.processing_status}">${book.processing_status}</span>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            alert(error.message);
        }
    }

    async loadSystemSettings() {
        try {
            const settings = await this.apiCall('/settings');
            const form = document.getElementById('systemSettingsForm');
            for (const [key, value] of Object.entries(settings)) {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) input.value = value;
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    async saveSystemSettings() {
        try {
            const form = document.getElementById('systemSettingsForm');
            const formData = new FormData(form);
            const settings = {};
            formData.forEach((value, key) => settings[key] = value);

            await this.apiCall('/settings', {
                method: 'POST',
                body: JSON.stringify(settings)
            });
            alert('Settings saved successfully');
        } catch (error) {
            alert(error.message);
        }
    }

    async loadReaders() {
        try {
            const readers = await this.apiCall('/readers');
            const tbody = document.getElementById('readersTableBody');
            tbody.innerHTML = readers.map(reader => `
                <tr>
                    <td><span class="user-id">#${reader.id}</span></td>
                    <td>
                        <div class="user-info-cell">
                            <div class="user-avatar-small">${reader.username.charAt(0).toUpperCase()}</div>
                            <span>${reader.username}</span>
                        </div>
                    </td>
                    <td>${reader.email}</td>
                    <td><span class="badge badge-reader">Reader</span></td>
                    <td>
                        <button class="btn btn-primary btn-sm" onclick="adminApp.viewReaderDetails(${reader.id})">
                            <i class="fas fa-eye"></i> View Details
                        </button>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            alert(error.message);
        }
    }

    async viewReaderDetails(userId) {
        try {
            const data = await this.apiCall(`/readers/${userId}/details`);
            const { user, subscriptions, usage_stats } = data;
            
            this.switchTab('readerDetails');
            document.getElementById('detailReaderName').textContent = user.username;
            
            document.getElementById('readerInfoContent').innerHTML = `
                <div class="info-row"><strong>Email:</strong> ${user.email}</div>
                <div class="info-row"><strong>Username:</strong> ${user.username}</div>
                <div class="info-row"><strong>Joined:</strong> ${new Date(user.created_at).toLocaleDateString()}</div>
                <div class="info-row"><strong>Status:</strong> <span class="status status-${user.is_active ? 'active' : 'inactive'}">${user.is_active ? 'Active' : 'Inactive'}</span></div>
            `;

            const subList = document.getElementById('readerSubscriptionsList');
            if (subscriptions.length === 0) {
                subList.innerHTML = '<p class="no-data">No active subscriptions.</p>';
            } else {
                subList.innerHTML = subscriptions.map(sub => `
                    <div class="subscription-item-admin">
                        <div class="sub-icon"><i class="fas fa-user-check"></i></div>
                        <div class="sub-info">
                            <strong>${sub.author_name}</strong>
                            <span>Subscribed on ${new Date(sub.subscribed_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                `).join('');
            }

            const usageStats = document.getElementById('readerUsageStats');
            usageStats.innerHTML = `
                <div class="mini-stats-grid">
                    <div class="mini-stat">
                        <label><i class="fas fa-coins"></i> Total Tokens</label>
                        <span>${usage_stats.total_tokens.toLocaleString()}</span>
                    </div>
                    <div class="mini-stat">
                        <label><i class="fas fa-dollar-sign"></i> Total Cost</label>
                        <span class="cost-text">$${usage_stats.total_cost.toFixed(4)}</span>
                    </div>
                    <div class="mini-stat">
                        <label><i class="fas fa-bolt"></i> Operations</label>
                        <span>${usage_stats.operations_count}</span>
                    </div>
                </div>
                <div class="usage-breakdown-mini mt-4">
                    <h4 class="mb-3">Operation Breakdown</h4>
                    <div class="breakdown-item">
                        <span><i class="fas fa-search"></i> Search</span>
                        <strong>$${usage_stats.breakdown.search_activity.cost.toFixed(4)}</strong>
                    </div>
                    <div class="breakdown-item">
                        <span><i class="fas fa-comments"></i> AI Chat</span>
                        <strong>$${usage_stats.breakdown.ai_conversations.cost.toFixed(4)}</strong>
                    </div>
                </div>
            `;
        } catch (error) {
            alert(error.message);
        }
    }

    async loadAdvancedUsageStats() {
        try {
            const userId = document.getElementById('usageFilterUser').value;
            const opType = document.getElementById('usageFilterOp').value;
            const days = document.getElementById('usageFilterDays').value;
            
            let url = `/usage/logs?days=${days}`;
            if (userId) url += `&user_id=${userId}`;
            if (opType) url += `&operation_type=${opType}`;
            
            const logs = await this.apiCall(url);
            const tbody = document.getElementById('usageLogsTableBody');
            
            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td><span class="timestamp">${new Date(log.timestamp).toLocaleString()}</span></td>
                    <td><span class="user-id">#${log.user_id}</span></td>
                    <td><span class="op-badge op-${log.operation_type}">${log.operation_type}</span></td>
                    <td><span class="model-name">${log.model_name}</span></td>
                    <td>${log.total_tokens.toLocaleString()}</td>
                    <td><span class="cost-text">$${log.cost_estimate.toFixed(6)}</span></td>
                    <td><span class="status status-${log.success ? 'active' : 'failed'}">${log.success ? 'Success' : 'Error'}</span></td>
                </tr>
            `).join('');

            // If first load, populate user filter
            if (document.getElementById('usageFilterUser').options.length <= 1) {
                this.populateUserFilter();
            }
        } catch (error) {
            alert(error.message);
        }
    }

    async populateUserFilter() {
        try {
            const users = await this.apiCall('/users');
            const select = document.getElementById('usageFilterUser');
            users.forEach(user => {
                const opt = document.createElement('option');
                opt.value = user.id;
                opt.textContent = `${user.username} (#${user.id})`;
                select.appendChild(opt);
            });
        } catch (error) {
            console.error('Error populating user filter:', error);
        }
    }

    // PDF Viewer Methods
    async viewBookPdf(bookId, title) {
        try {
            const modal = document.getElementById('pdfViewerModal');
            document.getElementById('pdfViewerTitle').textContent = title;
            modal.classList.remove('hidden');

            this.canvas = document.getElementById('pdfCanvas');
            this.ctx = this.canvas.getContext('2d');

            const url = `/api/v1/books/${bookId}/pdf`;
            const loadingTask = pdfjsLib.getDocument({
                url: url,
                httpHeaders: { 'Authorization': `Bearer ${this.token}` }
            });

            this.pdfDoc = await loadingTask.promise;
            this.pageNum = 1;
            this.renderPage(this.pageNum);
        } catch (error) {
            alert('Error loading PDF: ' + error.message);
        }
    }

    async renderPage(num) {
        this.pageRendering = true;
        const page = await this.pdfDoc.getPage(num);
        
        const viewport = page.getViewport({ scale: this.scale });
        this.canvas.height = viewport.height;
        this.canvas.width = viewport.width;

        const renderContext = {
            canvasContext: this.ctx,
            viewport: viewport
        };

        const renderTask = page.render(renderContext);
        await renderTask.promise;
        
        this.pageRendering = false;
        if (this.pageNumPending !== null) {
            this.renderPage(this.pageNumPending);
            this.pageNumPending = null;
        }

        document.getElementById('pageInfo').textContent = `Page ${num} of ${this.pdfDoc.numPages}`;
    }

    queueRenderPage(num) {
        if (this.pageRendering) {
            this.pageNumPending = num;
        } else {
            this.renderPage(num);
        }
    }

    prevPage() {
        if (this.pageNum <= 1) return;
        this.pageNum--;
        this.queueRenderPage(this.pageNum);
    }

    nextPage() {
        if (this.pageNum >= this.pdfDoc.numPages) return;
        this.pageNum++;
        this.queueRenderPage(this.pageNum);
    }

    zoomIn() {
        this.scale += 0.2;
        document.getElementById('zoomLevel').textContent = `${Math.round(this.scale * 100)}%`;
        this.renderPage(this.pageNum);
    }

    zoomOut() {
        if (this.scale <= 0.4) return;
        this.scale -= 0.2;
        document.getElementById('zoomLevel').textContent = `${Math.round(this.scale * 100)}%`;
        this.renderPage(this.pageNum);
    }

    closePdfViewer() {
        document.getElementById('pdfViewerModal').classList.add('hidden');
        this.pdfDoc = null;
    }
}

const adminApp = new AdminApp();
