/**
 * ============================================================================
 * CRUD DE USUARIOS - Panel de Administración
 * ============================================================================
 * Permite al ADMIN gestionar usuarios:
 *   - Listar con búsqueda, filtros por rol y estado, y paginación.
 *   - Crear usuarios con cualquier rol (CLIENTE o ADMIN).
 *   - Editar datos (incluido el rol).
 *   - Activar/desactivar (soft delete manual).
 *   - Eliminar con las siguientes reglas:
 *       • No puede eliminarse a sí mismo (botón deshabilitado).
 *       • El backend rechaza eliminar al último admin activo.
 *       • Si el usuario tiene órdenes asociadas, el backend hace soft delete
 *         automáticamente (responde 200 con `soft_deleted: true`).
 *
 * Reglas de UI aplicadas:
 *   - El username no es editable tras la creación.
 *   - La contraseña es opcional en edición.
 *   - Los usuarios archivados (soft deleted) se muestran con badge gris.
 * ============================================================================
 */

const UsersCRUD = {
    // --- Estado interno ---
    items: [],
    editingId: null,
    modal: null,
    currentPage: 1,
    searchTerm: '',
    searchTimer: null,

    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================

    async init() {
        this.modal = new bootstrap.Modal(document.getElementById('userModal'));
        await this.load();
    },

    // ========================================================================
    // CARGA DE DATOS
    // ========================================================================

    /**
     * Construye la URL con filtros aplicados.
     */
    buildUrl() {
        const params = new URLSearchParams();
        const role = document.getElementById('user-filter-role')?.value || '';
        const active = document.getElementById('user-filter-active')?.value || '';

        if (this.searchTerm) params.append('search', this.searchTerm);
        if (role) params.append('role', role);
        if (active) params.append('is_active', active);
        if (this.currentPage > 1) params.append('page', this.currentPage);

        const qs = params.toString();
        return '/api/users/' + (qs ? '?' + qs : '');
    },

    /**
     * Carga la lista de usuarios desde el backend.
     */
    async load() {
        const tbody = document.getElementById('users-tbody');
        if (!tbody) return;

        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <div class="spinner-border spinner-border-sm text-primary"></div>
                    Cargando usuarios...
                </td>
            </tr>`;

        try {
            const data = await API.get(this.buildUrl());
            this.items = data.results || data;
            this.render();
            this.renderPagination(data);
        } catch (e) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger py-4">
                        <i class="bi bi-exclamation-circle"></i>
                        Error al cargar usuarios: ${e.data?.detail || 'Error desconocido'}
                    </td>
                </tr>`;
        }
    },

    // ========================================================================
    // RENDERIZADO
    // ========================================================================

    /**
     * Renderiza la tabla de usuarios.
     */
    render() {
        const tbody = document.getElementById('users-tbody');
        const me = API.getUser();

        if (this.items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="bi bi-people fs-3 d-block mb-2"></i>
                        No hay usuarios que coincidan con los filtros
                    </td>
                </tr>`;
            return;
        }

        tbody.innerHTML = this.items.map(u => this.renderRow(u, me)).join('');
    },

    /**
     * Renderiza una fila de usuario.
     */
    renderRow(u, me) {
        const isMe = me && me.user_id === u.id;
        const isSoftDeleted = u.username.startsWith('deleted_');

        // --- Nombre visual (limpia el prefijo de soft delete) ---
        const displayUsername = isSoftDeleted
            ? u.username.replace(/^deleted_\d+_/, '')
            : u.username;

        const displayEmail = isSoftDeleted
            ? '—'
            : u.email;

        // --- Badge de rol ---
        const roleBadge = u.role === 'ADMIN'
            ? '<span class="badge bg-danger"><i class="bi bi-shield-fill"></i> Admin</span>'
            : '<span class="badge bg-info"><i class="bi bi-person-fill"></i> Cliente</span>';

        // --- Badge de estado (3 estados posibles) ---
        let statusBadge;
        if (isSoftDeleted) {
            statusBadge = `
                <span class="badge bg-dark" title="Desactivado al tener órdenes asociadas">
                    <i class="bi bi-archive-fill"></i> Archivado
                </span>`;
        } else if (u.is_active) {
            statusBadge = '<span class="badge bg-success"><i class="bi bi-check-circle-fill"></i> Activo</span>';
        } else {
            statusBadge = '<span class="badge bg-secondary"><i class="bi bi-pause-circle-fill"></i> Inactivo</span>';
        }

        // --- Badge "Tú" para el usuario actual ---
        const youBadge = isMe
            ? '<span class="badge bg-primary ms-2" style="font-size:0.65rem;">TÚ</span>'
            : '';

        // --- Fecha ---
        const date = new Date(u.date_joined).toLocaleDateString('es-CL', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
        });

        return `
            <tr>
                <td><code class="small">#${u.id}</code></td>
                <td>
                    <div class="fw-semibold">
                        ${escapeHtml(displayUsername)}
                        ${youBadge}
                    </div>
                    <small class="text-muted">${escapeHtml(displayEmail)}</small>
                </td>
                <td>
                    <div>${escapeHtml(u.full_name || '—')}</div>
                    <small class="text-muted">${escapeHtml(u.rut || '')}</small>
                </td>
                <td>${roleBadge}</td>
                <td>${statusBadge}</td>
                <td class="text-muted small">${date}</td>
                <td class="text-end">
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary"
                                onclick="UsersCRUD.openEdit(${u.id})"
                                title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger"
                                onclick="UsersCRUD.remove(${u.id})"
                                ${isMe ? 'disabled title="No puedes eliminarte a ti mismo"' : ''}
                                title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    },

    /**
     * Renderiza la paginación.
     */
    renderPagination(data) {
        const container = document.getElementById('users-pagination');
        if (!container) return;

        if (!data.next && !data.previous) {
            container.innerHTML = '';
            return;
        }

        const total = data.count || 0;
        const pageSize = 10;
        const totalPages = Math.ceil(total / pageSize);

        container.innerHTML = `
            <nav>
                <ul class="pagination justify-content-center mb-0">
                    <li class="page-item ${!data.previous ? 'disabled' : ''}">
                        <a class="page-link" href="#"
                           onclick="UsersCRUD.goPage(${this.currentPage - 1}); return false;">
                            <i class="bi bi-chevron-left"></i>
                        </a>
                    </li>
                    <li class="page-item active">
                        <span class="page-link">
                            Página ${this.currentPage} de ${totalPages}
                        </span>
                    </li>
                    <li class="page-item ${!data.next ? 'disabled' : ''}">
                        <a class="page-link" href="#"
                           onclick="UsersCRUD.goPage(${this.currentPage + 1}); return false;">
                            <i class="bi bi-chevron-right"></i>
                        </a>
                    </li>
                </ul>
            </nav>`;
    },

    // ========================================================================
    // FILTROS Y PAGINACIÓN
    // ========================================================================

    goPage(page) {
        if (page < 1) return;
        this.currentPage = page;
        this.load();
    },

    /**
     * Búsqueda con debounce (evita múltiples requests al tipear).
     */
    debouncedSearch() {
        clearTimeout(this.searchTimer);
        this.searchTimer = setTimeout(() => {
            this.searchTerm = document.getElementById('user-search').value.trim();
            this.currentPage = 1;
            this.load();
        }, 400);
    },

    /**
     * Limpia todos los filtros.
     */
    clearFilters() {
        const search = document.getElementById('user-search');
        const role = document.getElementById('user-filter-role');
        const active = document.getElementById('user-filter-active');

        if (search) search.value = '';
        if (role) role.value = '';
        if (active) active.value = '';

        this.searchTerm = '';
        this.currentPage = 1;
        this.load();
    },

    // ========================================================================
    // CREAR USUARIO
    // ========================================================================

    openCreate() {
        this.editingId = null;

        document.getElementById('userModalTitle').innerHTML =
            '<i class="bi bi-person-plus"></i> Nuevo Usuario';
        document.getElementById('user-form').reset();
        document.getElementById('user-id').value = '';

        // Habilitar username en creación
        document.getElementById('user-username').disabled = false;

        // Valores por defecto
        document.getElementById('user-is-active').checked = true;
        document.getElementById('user-is-staff').checked = false;
        document.getElementById('user-role').value = 'CLIENTE';

        // Marcar password como obligatorio en creación
        document.getElementById('password-required-mark').style.display = 'inline';
        document.getElementById('password-help').textContent =
            'Obligatoria al crear. Mínimo 8 caracteres.';

        this.modal.show();
    },

    // ========================================================================
    // EDITAR USUARIO
    // ========================================================================

    async openEdit(id) {
        try {
            const u = await API.get(`/api/users/${id}/`);
            this.editingId = id;

            document.getElementById('userModalTitle').innerHTML =
                '<i class="bi bi-pencil"></i> Editar Usuario';
            document.getElementById('user-id').value = u.id;
            document.getElementById('user-username').value = u.username;
            document.getElementById('user-username').disabled = true;   // No editable
            document.getElementById('user-email').value = u.email || '';
            document.getElementById('user-first-name').value = u.first_name || '';
            document.getElementById('user-last-name').value = u.last_name || '';
            document.getElementById('user-rut').value = u.rut || '';
            document.getElementById('user-phone').value = u.phone || '';
            document.getElementById('user-role').value = u.role;
            document.getElementById('user-is-active').checked = u.is_active;
            document.getElementById('user-is-staff').checked = u.is_staff;
            document.getElementById('user-password').value = '';

            // Password opcional en edición
            document.getElementById('password-required-mark').style.display = 'none';
            document.getElementById('password-help').textContent =
                'Opcional. Dejar vacío para no cambiar la contraseña.';

            this.modal.show();
        } catch (e) {
            showFlash('Error al cargar el usuario.', 'danger');
        }
    },

    // ========================================================================
    // GUARDAR (crear o editar)
    // ========================================================================

    async save(event) {
        event.preventDefault();

        // --- Construir payload ---
        const payload = {
            email: document.getElementById('user-email').value.trim(),
            first_name: document.getElementById('user-first-name').value.trim(),
            last_name: document.getElementById('user-last-name').value.trim(),
            rut: document.getElementById('user-rut').value.trim() || null,
            phone: document.getElementById('user-phone').value.trim() || null,
            role: document.getElementById('user-role').value,
            is_active: document.getElementById('user-is-active').checked,
            is_staff: document.getElementById('user-is-staff').checked,
        };

        // Username solo se envía al crear
        if (!this.editingId) {
            payload.username = document.getElementById('user-username').value.trim();
        }

        // Password solo se envía si no está vacío
        const password = document.getElementById('user-password').value;
        if (password) {
            payload.password = password;
        }

        // --- Validaciones locales ---
        if (!payload.email) {
            showFlash('El email es obligatorio.', 'warning');
            return;
        }
        if (!this.editingId && !payload.username) {
            showFlash('El username es obligatorio.', 'warning');
            return;
        }
        if (!this.editingId && !password) {
            showFlash('La contraseña es obligatoria al crear un usuario.', 'warning');
            return;
        }
        if (password && password.length < 8) {
            showFlash('La contraseña debe tener al menos 8 caracteres.', 'warning');
            return;
        }

        // --- Enviar al backend ---
        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';

        try {
            if (this.editingId) {
                await API.patch(`/api/users/${this.editingId}/`, payload);
                showFlash('Usuario actualizado correctamente.', 'success');
            } else {
                await API.post('/api/users/', payload);
                showFlash('Usuario creado correctamente.', 'success');
            }
            this.modal.hide();
            await this.load();
        } catch (e) {
            const errs = e.data || {};
            let msg = 'Error al guardar el usuario.';

            if (typeof errs === 'string') {
                msg = errs;
            } else {
                const firstKey = Object.keys(errs)[0];
                if (firstKey) {
                    const val = errs[firstKey];
                    msg = Array.isArray(val) ? val[0] : val;
                } else if (errs.detail) {
                    msg = errs.detail;
                }
            }
            showFlash(msg, 'danger');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
        }
    },

    // ========================================================================
    // ELIMINAR USUARIO (con soft delete automático)
    // ========================================================================

    async remove(id) {
        const u = this.items.find(x => x.id === id);
        if (!u) return;

        // --- Construir mensaje de confirmación ---
        const confirmMsg = [
            `¿Eliminar al usuario "${u.username}"?`,
            '',
            '⚠️ Si el usuario tiene órdenes asociadas, se DESACTIVARÁ',
            'en lugar de eliminarse para preservar el histórico de compras.',
            '',
            'Esta acción no se puede deshacer.',
        ].join('\n');

        if (!confirm(confirmMsg)) return;

        try {
            const response = await API.delete(`/api/users/${id}/`);

            // El backend devuelve 200 con `soft_deleted: true` si tenía órdenes
            if (response && response.soft_deleted) {
                showFlash(
                    response.detail || 'Usuario archivado por tener órdenes asociadas.',
                    'warning'
                );
            } else {
                // 204 No Content: eliminación física normal
                showFlash('Usuario eliminado correctamente.', 'success');
            }

            await this.load();
        } catch (e) {
            let msg = 'No se puede eliminar este usuario.';

            if (e.data?.detail) {
                msg = e.data.detail;
            } else if (e.status === 403) {
                msg = e.data?.detail || 'No tienes permiso para eliminar este usuario.';
            } else if (e.status === 404) {
                msg = 'El usuario ya no existe.';
                await this.load();
            } else if (e.status === 409) {
                msg = e.data?.detail || 'El usuario tiene registros asociados.';
            }

            showFlash(msg, 'danger');
        }
    },
};

// ============================================================================
// INICIALIZACIÓN
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('users-tbody')) {
        UsersCRUD.init();
    }
});