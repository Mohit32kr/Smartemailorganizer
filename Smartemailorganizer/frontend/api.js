class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.token = localStorage.getItem('token');
    }

    async login(email, password) {
        const response = await fetch(`${this.baseURL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Login failed');
        }

        const data = await response.json();
        this.token = data.access_token;
        localStorage.setItem('token', this.token);
        return data;
    }

    async getEmails(page = 1, category = null, pageSize = 20) {
        const params = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString()
        });

        if (category && category !== 'all') {
            params.append('category', category);
        }

        const response = await this._fetchWithAuth(`${this.baseURL}/api/emails?${params}`);
        return response;
    }

    async searchEmails(query) {
        const params = new URLSearchParams({ query });
        const response = await this._fetchWithAuth(`${this.baseURL}/api/emails/search?${params}`);
        return response;
    }

    async sendEmail(to, subject, body) {
        const response = await this._fetchWithAuth(`${this.baseURL}/api/emails/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ to, subject, body })
        });
        return response;
    }

    async syncEmails() {
        const response = await this._fetchWithAuth(`${this.baseURL}/api/emails/sync`, {
            method: 'POST'
        });
        return response;
    }

    async getEmailById(id) {
        const response = await this._fetchWithAuth(`${this.baseURL}/api/emails/${id}`);
        return response;
    }

    async getStats() {
        const response = await this._fetchWithAuth(`${this.baseURL}/api/stats`);
        return response;
    }

    async _fetchWithAuth(url, options = {}) {
        if (!this.token) {
            this._redirectToLogin();
            throw new Error('No authentication token');
        }

        const headers = {
            ...options.headers,
            'Authorization': `Bearer ${this.token}`
        };

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('token');
            this.token = null;
            this._redirectToLogin();
            throw new Error('Authentication failed');
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Request failed');
        }

        return response.json();
    }

    _redirectToLogin() {
        window.location.href = '/login.html';
    }

    logout() {
        localStorage.removeItem('token');
        this.token = null;
        this._redirectToLogin();
    }
}
