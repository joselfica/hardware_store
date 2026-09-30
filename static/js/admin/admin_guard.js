/**
 * ============================================================================
 * GUARD DE ROL - Protege las páginas del panel admin
 * ============================================================================
 * Este script se ejecuta ANTES de cualquier otro en las páginas de
 * administración. Verifica que:
 *   1. El usuario esté autenticado (tiene token válido).
 *   2. El token contenga el claim role === 'ADMIN'.
 *
 * Si alguna falla, redirige al login o al inicio con un mensaje.
 *
 * ⚠️ SEGURIDAD: Este guard es UX, no seguridad. La seguridad REAL está en
 * el backend, donde cada endpoint de escritura exige IsAdminRole.
 * ============================================================================
 */

(function guardAdminPanel() {
    const token = localStorage.getItem('access_token');

    // --- 1. ¿Está autenticado? ---
    if (!token) {
        sessionStorage.setItem('redirect_after_login', window.location.pathname);
        window.location.href = '/login/';
        return;
    }

    // --- 2. ¿El token es válido y tiene role ADMIN? ---
    try {
        const payload = JSON.parse(
            atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))
        );

        // Verificar expiración
        if (payload.exp * 1000 < Date.now()) {
            localStorage.clear();
            window.location.href = '/login/';
            return;
        }

        // Verificar rol
        if (payload.role !== 'ADMIN') {
            alert('⛔ Acceso denegado. Se requiere rol de Administrador.');
            window.location.href = '/';
            return;
        }
    } catch (e) {
        localStorage.clear();
        window.location.href = '/login/';
    }
})();