class InboxManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.currentPage = 1;
        this.currentCategory = 'all';
        this.pageSize = 20;
        this.isSearchMode = false;
        this.currentSearchQuery = '';
        
        this.initializeEventListeners();
        this.loadEmails();
    }

    initializeEventListeners() {
        // Category filter buttons
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const category = e.target.dataset.category;
                this.handleCategoryFilter(category);
            });
        });

        // Search functionality
        document.getElementById('searchBtn').addEventListener('click', () => {
            this.handleSearch();
        });

        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });

        document.getElementById('clearSearchBtn').addEventListener('click', () => {
            document.getElementById('searchInput').value = '';
            this.isSearchMode = false;
            this.currentSearchQuery = '';
            this.loadEmails();
        });

        // Sync button
        document.getElementById('syncBtn').addEventListener('click', () => {
            this.handleSync();
        });

        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.apiClient.logout();
        });

        // Compose button
        document.getElementById('composeBtn').addEventListener('click', () => {
            this.showComposeModal();
        });

        // Send email button
        document.getElementById('sendEmailBtn').addEventListener('click', () => {
            this.handleCompose();
        });

        // Pagination
        document.getElementById('prevPage').addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage > 1) {
                this.currentPage--;
                this.loadEmails();
            }
        });

        document.getElementById('nextPage').addEventListener('click', (e) => {
            e.preventDefault();
            this.currentPage++;
            this.loadEmails();
        });
    }

    async loadEmails() {
        try {
            this.showLoading(true);
            
            let data;
            if (this.isSearchMode) {
                data = await this.apiClient.searchEmails(this.currentSearchQuery);
                // Search doesn't have pagination in the current API
                data = { emails: data, total: data.length, page: 1, page_size: data.length };
            } else {
                data = await this.apiClient.getEmails(this.currentPage, this.currentCategory, this.pageSize);
            }

            this.renderEmailList(data.emails);
            this.updatePagination(data);
            this.updateEmailCount(data.total);
            
            this.showLoading(false);
        } catch (error) {
            this.showLoading(false);
            showToast('Failed to load emails: ' + error.message, 'error');
        }
    }

    renderEmailList(emails) {
        const tbody = document.getElementById('emailTableBody');
        tbody.innerHTML = '';

        if (emails.length === 0) {
            document.getElementById('emailListContainer').classList.add('d-none');
            document.getElementById('emptyState').classList.remove('d-none');
            return;
        }

        document.getElementById('emailListContainer').classList.remove('d-none');
        document.getElementById('emptyState').classList.add('d-none');

        emails.forEach(email => {
            const row = document.createElement('tr');
            row.style.cursor = 'pointer';
            row.addEventListener('click', () => this.showEmailDetail(email.id));

            const categoryClass = this.getCategoryClass(email.category);
            
            row.innerHTML = `
                <td>${this.escapeHtml(email.sender)}</td>
                <td>${this.escapeHtml(email.subject)}</td>
                <td><span class="badge ${categoryClass}">${email.category}</span></td>
                <td>${this.formatDate(email.date)}</td>
            `;

            tbody.appendChild(row);
        });
    }

    async showEmailDetail(emailId) {
        try {
            const email = await this.apiClient.getEmailById(emailId);
            this.renderEmailDetail(email);
            
            const modal = new bootstrap.Modal(document.getElementById('emailDetailModal'));
            modal.show();
        } catch (error) {
            showToast('Failed to load email details: ' + error.message, 'error');
        }
    }

    renderEmailDetail(email) {
        document.getElementById('emailDetailSubject').textContent = email.subject;
        document.getElementById('emailDetailSender').textContent = email.sender;
        document.getElementById('emailDetailDate').textContent = this.formatDate(email.date);
        
        const categoryBadge = document.getElementById('emailDetailCategory');
        categoryBadge.textContent = email.category;
        categoryBadge.className = `badge ${this.getCategoryClass(email.category)}`;
        
        document.getElementById('emailDetailBody').textContent = email.body;
    }

    handleCategoryFilter(category) {
        // Update active button
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.category === category) {
                btn.classList.add('active');
            }
        });

        this.currentCategory = category;
        this.currentPage = 1;
        this.isSearchMode = false;
        this.loadEmails();
    }

    async handleSearch() {
        const query = document.getElementById('searchInput').value.trim();
        
        if (!query) {
            showToast('Please enter a search query', 'error');
            return;
        }

        this.isSearchMode = true;
        this.currentSearchQuery = query;
        this.currentPage = 1;
        this.loadEmails();
    }

    async handleSync() {
        const syncBtn = document.getElementById('syncBtn');
        const syncIcon = document.getElementById('syncIcon');
        
        try {
            syncBtn.disabled = true;
            syncIcon.classList.add('spinning');
            
            const result = await this.apiClient.syncEmails();
            
            showToast(`Sync completed! Fetched ${result.fetched} emails, classified ${result.classified}`, 'success');
            
            // Reload emails after sync
            this.loadEmails();
        } catch (error) {
            showToast('Sync failed: ' + error.message, 'error');
        } finally {
            syncBtn.disabled = false;
            syncIcon.classList.remove('spinning');
        }
    }

    showComposeModal() {
        // Clear form
        document.getElementById('composeForm').reset();
        
        const modal = new bootstrap.Modal(document.getElementById('composeModal'));
        modal.show();
    }

    async handleCompose() {
        const to = document.getElementById('composeTo').value.trim();
        const subject = document.getElementById('composeSubject').value.trim();
        const body = document.getElementById('composeBody').value.trim();

        if (!to || !subject || !body) {
            showToast('Please fill in all fields', 'error');
            return;
        }

        try {
            const sendBtn = document.getElementById('sendEmailBtn');
            sendBtn.disabled = true;
            sendBtn.textContent = 'Sending...';

            await this.apiClient.sendEmail(to, subject, body);
            
            showToast('Email sent successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('composeModal'));
            modal.hide();
            
            // Reset form
            document.getElementById('composeForm').reset();
        } catch (error) {
            showToast('Failed to send email: ' + error.message, 'error');
        } finally {
            const sendBtn = document.getElementById('sendEmailBtn');
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
        }
    }

    updatePagination(data) {
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        const pageInfo = document.getElementById('pageInfo');

        // Update page info
        const totalPages = Math.ceil(data.total / data.page_size) || 1;
        pageInfo.textContent = `Page ${data.page} of ${totalPages}`;

        // Update prev button
        if (data.page > 1) {
            prevBtn.classList.remove('disabled');
        } else {
            prevBtn.classList.add('disabled');
        }

        // Update next button
        if (data.page < totalPages) {
            nextBtn.classList.remove('disabled');
        } else {
            nextBtn.classList.add('disabled');
        }
    }

    updateEmailCount(total) {
        document.getElementById('emailCount').textContent = `${total} email${total !== 1 ? 's' : ''}`;
    }

    showLoading(show) {
        const spinner = document.getElementById('loadingSpinner');
        const container = document.getElementById('emailListContainer');
        
        if (show) {
            spinner.classList.remove('d-none');
            container.classList.add('d-none');
        } else {
            spinner.classList.add('d-none');
            container.classList.remove('d-none');
        }
    }

    getCategoryClass(category) {
        const classes = {
            'Work': 'bg-primary',
            'Personal': 'bg-success',
            'Spam': 'bg-danger',
            'Promotions': 'bg-warning text-dark'
        };
        return classes[category] || 'bg-secondary';
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return date.toLocaleDateString('en-US', { weekday: 'short' });
        } else {
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the inbox manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const apiClient = new APIClient();
    new InboxManager(apiClient);
});
