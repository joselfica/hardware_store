/**
 * ============================================================================
 * PERFIL DE USUARIO
 * ============================================================================
 * Permite al usuario autenticado:
 *   - Ver y editar sus datos personales (nombre, email, RUT, teléfono).
 *   - Cambiar su contraseña.
 *
 * El username y el rol son de solo lectura.
 *
 * Autor: José Fica
 * Sección: AP-N4-C2
 * Año: 2026
 * ============================================================================
 */

const Profile = {
    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================

    async init() {
        if (!API.isAuthenticated()) {
            showFlash('Debes iniciar sesión para ver tu perfil.', 'warning');
            setTimeout(() => window.location.href = '/login/', 800);
            return;
        }
        await this.load();
    },

    // ========================================================================
    // CARGA DE DATOS
    // ========================================================================

    async load() {
        try {
            const user = await API.get('/api/auth/me/');

            document.getElementById('profile-username').value = user.username;
            document.getElementById('profile-role').value = user.role_display || user.role;
            document.getElementById('profile-first-name').value = user.first_name || '';
            document.getElementById('profile-last-name').value = user.last_name || '';
            document.getElementById('profile-email').value = user.email || '';
            document.getElementById('profile-rut').value = user.rut || '';
            document.getElementById('profile-phone').value = user.phone || '';
        } catch (e) {
            showFlash('Error al cargar el perfil.', 'danger');
        }
    },

    // ========================================================================
    // GUARDAR DATOS
    // ========================================================================

    async save(event) {
        event.preventDefault();

        const payload = {
            first_name: document.getElementById('profile-first-name').value.trim(),
            last_name: document.getElementById('profile-last-name').value.trim(),
            email: document.getElementById('profile-email').value.trim(),
            rut: document.getElementById('profile-rut').value.trim() || null,
            phone: document.getElementById('profile-phone').value.trim() || null,
        };

        if (!payload.email) {
            showFlash('El email es obligatorio.', 'warning');
            return;
        }

        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';

        try {
            await API.patch('/api/auth/me/', payload);
            showFlash('Perfil actualizado correctamente.', 'success');
            await this.load();
        } catch (e) {
            const errs = e.data || {};
            const msg = Object.entries(errs)
                .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
                .join(' · ') || 'Error al guardar.';
            showFlash(msg, 'danger');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
        }
    },

    // ========================================================================
    // CAMBIAR CONTRASEÑA
    // ========================================================================

    async changePassword(event) {
        event.preventDefault();

        const oldPassword = document.getElementById('profile-old-password').value;
        const newPassword = document.getElementById('profile-new-password').value;
        const newPasswordConfirm = document.getElementById('profile-new-password-confirm').value;

        if (newPassword !== newPasswordConfirm) {
            showFlash('Las nuevas contraseñas no coinciden.', 'warning');
            return;
        }

        if (newPassword.length < 8) {
            showFlash('La nueva contraseña debe tener al menos 8 caracteres.', 'warning');
            return;
        }

        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Cambiando...';

        try {
            await API.post('/api/auth/change-password/', {
                old_password: oldPassword,
                new_password: newPassword,
                new_password_confirm: newPasswordConfirm,
            });
            showFlash('Contraseña actualizada correctamente.', 'success');
            event.target.reset();
        } catch (e) {
            const errs = e.data || {};
            const msg = Object.entries(errs)
                .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
                .join(' · ') || 'Error al cambiar la contraseña.';
            showFlash(msg, 'danger');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
        }
    },
};

// ============================================================================
// INICIALIZACIÓN
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('profile-form')) Profile.init();
});