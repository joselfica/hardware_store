/**
 * ============================================================================
 * AUTENTICACIÓN - Login, registro, logout y estado del navbar
 * ============================================================================
 * Se apoya en API (api.js) para las peticiones y en localStorage para
 * persistir los tokens. Actualiza el navbar según el estado de sesión.
 *
 * Puntos de entrada de initNavbar():
 *   1. DOMContentLoaded (evento normal).
 *   2. setTimeout(0) de respaldo (por si el DOM no estaba listo).
 *   3. Llamada manual desde login() tras guardar tokens.
 *   4. Llamada manual desde logout() tras limpiar tokens.
 * ============================================================================
 */

const Auth = {
    /**
     * Inicializa el estado del navbar según la sesión actual.
     * Idempotente: se puede llamar múltiples veces sin efectos adversos.
     */
    initNavbar() {
        const user = API.getUser();

        // Referencias a los elementos del navbar
        const navLogin    = document.getElementById('nav-login');
        const navUser     = document.getElementById('nav-user');
        const navCart     = document.getElementById('nav-cart');
        const navMyOrders = document.getElementById('nav-my-orders');
        const navAdmin    = document.getElementById('nav-admin-panel');

        // Si no existe el navbar en esta página, salimos silenciosamente
        if (!navLogin || !navUser) {
            return;
        }

        if (user) {
            // ---- Usuario autenticado ----
            navLogin.style.display    = 'none';
            navUser.style.display     = 'block';
            navCart.style.display     = 'block';
            if (navMyOrders) navMyOrders.style.display = 'block';
            if (navAdmin)    navAdmin.style.display    = (user.role === 'ADMIN') ? 'block' : 'none';

            const usernameEl = document.getElementById('nav-username');
            const roleEl     = document.getElementById('nav-role');
            const fullNameEl = document.getElementById('nav-full-name');

            if (usernameEl) usernameEl.textContent = user.username || 'Usuario';
            if (roleEl) {
                roleEl.textContent = user.role === 'ADMIN'
                    ? '👑 Administrador de TI'
                    : '🛒 Cliente';
            }
            if (fullNameEl) fullNameEl.textContent = user.full_name || user.username || '—';

            // Actualizar badge del carro
            this.updateCartBadge();

        } else {
            // ---- Usuario NO autenticado ----
            navLogin.style.display    = 'block';
            navUser.style.display     = 'none';
            navCart.style.display     = 'none';
            if (navMyOrders) navMyOrders.style.display = 'none';
            if (navAdmin)    navAdmin.style.display    = 'none';

            // Ocultar badge del carro
            const badge = document.getElementById('cart-badge');
            if (badge) badge.style.display = 'none';
        }
    },

    /**
     * Actualiza el badge del carro (cantidad de ítems).
     */
    async updateCartBadge() {
        if (!API.isAuthenticated()) return;
        try {
            const data = await API.get('/api/cart/summary/');
            const badge = document.getElementById('cart-badge');
            if (!badge) return;
            if (data.total_items > 0) {
                badge.textContent = data.total_items;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        } catch (e) {
            // Silencioso
        }
    },

    /**
     * Login: POST /api/auth/login/
     */
    async login(event) {
        event.preventDefault();
        const form = event.target;
        const username = form.username.value.trim();
        const password = form.password.value;

        try {
            const data = await API.post('/api/auth/login/', { username, password });
            API.setTokens(data.access, data.refresh);
            showFlash(`¡Bienvenido, ${data.user.full_name || data.user.username}!`, 'success');

            // Redirigir después de un breve delay para que el flash sea visible
            setTimeout(() => {
                window.location.href = '/';
            }, 800);
        } catch (err) {
            const msg = err.data?.detail || 'Credenciales inválidas.';
            showFlash(msg, 'danger');
        }
    },

    /**
     * Registro: POST /api/auth/register/
     */
    async register(event) {
        event.preventDefault();
        const form = event.target;
        const payload = {
            username: form.username.value.trim(),
            email: form.email.value.trim(),
            first_name: form.first_name.value.trim(),
            last_name: form.last_name.value.trim(),
            rut: form.rut.value.trim() || null,
            phone: form.phone.value.trim() || null,
            password: form.password.value,
            password_confirm: form.password_confirm.value,
        };

        try {
            const data = await API.post('/api/auth/register/', payload);
            API.setTokens(data.access, data.refresh);
            showFlash('¡Cuenta creada exitosamente!', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 800);
        } catch (err) {
            const errors = err.data || {};
            const firstError = Object.values(errors)[0];
            const msg = Array.isArray(firstError) ? firstError[0] : (firstError || 'Error al registrar.');
            showFlash(msg, 'danger');
        }
    },

    /**
     * Logout: POST /api/auth/logout/ + limpieza local.
     */
    async logout(event) {
        if (event) event.preventDefault();
        try {
            await API.post('/api/auth/logout/', { refresh: API.getRefresh() });
        } catch (e) {
            // Ignoramos errores: igual limpiamos localmente
        }
        API.clearTokens();
        showFlash('Sesión cerrada.', 'info');
        setTimeout(() => {
            window.location.href = '/';
        }, 600);
    },
};

// ============================================================================
// INICIALIZACIÓN DEL NAVBAR - Múltiples puntos de entrada
// ============================================================================
// 1. Ejecutar al cargar el DOM
document.addEventListener('DOMContentLoaded', () => Auth.initNavbar());

// 2. Respaldo: ejecutar en el siguiente tick por si el DOM tarda
setTimeout(() => {
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        Auth.initNavbar();
    }
}, 100);

// 3. Respaldo final: ejecutar tras window.load (todos los recursos cargados)
window.addEventListener('load', () => Auth.initNavbar());