/**
 * ============================================================================
 * CLIENTE API - Manejo centralizado de peticiones HTTP con JWT
 * ============================================================================
 * Este módulo encapsula:
 *   - Almacenamiento y recuperación de tokens JWT (localStorage).
 *   - Inyección automática del header Authorization.
 *   - Refresco automático del access token cuando expira (401).
 *   - Manejo uniforme de errores y mensajes flash.
 *   - Decodificación del payload JWT para leer los claims.
 *
 * Uso:
 *   const data = await API.get('/api/products/');
 *   const res = await API.post('/api/cart/items/', { product_id: 1, quantity: 2 });
 * ============================================================================
 */

const API_BASE = ''; // Mismo origen (Django sirve API y frontend)

const API = {
    // --- Almacenamiento de tokens ---
    getAccess()    { return localStorage.getItem('access_token'); },
    getRefresh()   { return localStorage.getItem('refresh_token'); },
    setTokens(access, refresh) {
        localStorage.setItem('access_token', access);
        if (refresh) localStorage.setItem('refresh_token', refresh);
    },
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
    },

    // --- Decodificar payload JWT (para leer claims como role) ---
    decodeToken(token) {
        try {
            const payload = token.split('.')[1];
            return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
        } catch (e) {
            return null;
        }
    },

    // --- Obtener datos del usuario desde el token ---
    getUser() {
        const token = this.getAccess();
        if (!token) return null;
        const payload = this.decodeToken(token);
        if (!payload || (payload.exp * 1000) < Date.now()) return null;
        return payload;
    },

    // --- ¿El usuario está autenticado? ---
    isAuthenticated() {
        return this.getUser() !== null;
    },

    // --- ¿El usuario es ADMIN? ---
    isAdmin() {
        const user = this.getUser();
        return user && user.role === 'ADMIN';
    },

    // --- Refrescar access token ---
    async refreshAccessToken() {
        const refresh = this.getRefresh();
        if (!refresh) return false;

        try {
            const res = await fetch(`${API_BASE}/api/auth/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh }),
            });
            if (!res.ok) throw new Error('Refresh failed');
            const data = await res.json();
            this.setTokens(data.access, data.refresh || refresh);
            return true;
        } catch (e) {
            this.clearTokens();
            return false;
        }
    },

    // --- Petición HTTP genérica con reintento automático por 401 ---
    //
    // Parámetros:
    //   method:    'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
    //   url:       Ruta relativa (ej: '/api/products/')
    //   body:      Objeto JS (se serializa a JSON) o FormData (para archivos)
    //   retry:     Interno, para reintentar tras refrescar el token
    //   isFormData: True si el body es un FormData (subida de archivos).
    //               En ese caso NO se setea Content-Type: el navegador lo
    //               hace automáticamente con el boundary correcto.
    async request(method, url, body = null, retry = true, isFormData = false) {
        const headers = {};

        // Si NO es FormData, usar JSON.
        // Si SÍ es FormData, dejar que el navegador setee Content-Type.
        if (!isFormData) {
            headers['Content-Type'] = 'application/json';
        }

        const token = this.getAccess();
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const options = { method, headers };
        if (body) {
            options.body = isFormData ? body : JSON.stringify(body);
        }

        let res = await fetch(`${API_BASE}${url}`, options);

        // Si el token expiró → intentar refrescar y reintentar una vez
        if (res.status === 401 && retry) {
            const refreshed = await this.refreshAccessToken();
            if (refreshed) {
                return this.request(method, url, body, false, isFormData);
            }
            this.clearTokens();
            window.location.href = '/login/';
            throw new Error('Sesión expirada');
        }

        // 204 No Content
        if (res.status === 204) return null;

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
            throw { status: res.status, data };
        }
        return data;
    },

    // --- Atajos ---
    get(url)         { return this.request('GET', url); },
    post(url, body)  { return this.request('POST', url, body); },
    patch(url, body) { return this.request('PATCH', url, body); },
    put(url, body)   { return this.request('PUT', url, body); },
    delete(url)      { return this.request('DELETE', url); },
};

/**
 * Muestra una alerta flash en la parte superior de la página.
 * @param {string} message - Texto del mensaje.
 * @param {string} type    - 'success' | 'danger' | 'warning' | 'info'
 */
function showFlash(message, type = 'info') {
    const container = document.getElementById('flash-messages');
    if (!container) return;
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show shadow-sm`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    container.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}

/**
 * Formatea un número como moneda chilena (CLP).
 */
function formatCLP(value) {
    return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        minimumFractionDigits: 0,
    }).format(value);
}

/**
 * Escapa HTML para prevenir XSS al inyectar datos de la API.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// EFECTOS DE SCROLL EN EL NAVBAR
// ============================================================================
document.addEventListener('scroll', () => {
    const navbar = document.getElementById('mainNavbar');
    if (navbar) {
        navbar.classList.toggle('scrolled', window.scrollY > 20);
    }
}, { passive: true });


/**
 * Muestra un spinner en un botón durante una operación async.
 * Restaura el estado original al terminar.
 *
 * Uso:
 *     await withButtonLoading(btn, () => API.post(...));
 */
async function withButtonLoading(btn, asyncFn, loadingText = 'Procesando...') {
    if (!btn) return asyncFn();

    const originalHTML = btn.innerHTML;
    const originalDisabled = btn.disabled;

    btn.disabled = true;
    btn.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        ${loadingText}
    `;

    try {
        return await asyncFn();
    } finally {
        btn.disabled = originalDisabled;
        btn.innerHTML = originalHTML;
    }
}