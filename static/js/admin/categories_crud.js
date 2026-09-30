/**
 * ============================================================================
 * CRUD DE CATEGORÍAS - Panel de Administración
 * ============================================================================
 * Implementa el CRUD completo desde el frontend:
 *   - Listar con búsqueda y paginación.
 *   - Crear mediante modal con formulario.
 *   - Editar mediante el mismo modal precargado.
 *   - Eliminar con confirmación.
 *
 * Solo accesible para usuarios con rol ADMIN (validado en admin_guard.js
 * y, a nivel real, en los permisos DRF del backend).
 * ============================================================================
 */

const CategoriesCRUD = {
    items: [],
    editingId: null,
    modal: null,

    async init() {
        this.modal = new bootstrap.Modal(document.getElementById('categoryModal'));
        await this.load();
    },

    async load() {
        const tbody = document.getElementById('categories-tbody');
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4">
            <div class="spinner-border spinner-border-sm text-primary"></div> Cargando...
        </td></tr>`;

        try {
            const data = await API.get('/api/categories/');
            this.items = data.results || data;
            this.render();
        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-4">
                Error al cargar categorías
            </td></tr>`;
        }
    },

    render() {
        const tbody = document.getElementById('categories-tbody');
        if (this.items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">
                No hay categorías registradas
            </td></tr>`;
            return;
        }

        tbody.innerHTML = this.items.map(c => `
            <tr>
                <td><code>#${c.id}</code></td>
                <td class="fw-semibold">${escapeHtml(c.name)}</td>
                <td class="text-muted small">${escapeHtml(c.slug)}</td>
                <td>
                    <span class="badge bg-${c.is_active ? 'success' : 'secondary'}">
                        ${c.is_active ? 'Activa' : 'Inactiva'}
                    </span>
                </td>
                <td>
                    <span class="badge bg-info">${c.products_count || 0}</span>
                </td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="CategoriesCRUD.openEdit(${c.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="CategoriesCRUD.remove(${c.id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    },

    openCreate() {
        this.editingId = null;
        document.getElementById('categoryModalTitle').innerHTML =
            '<i class="bi bi-plus-circle"></i> Nueva Categoría';
        document.getElementById('category-form').reset();
        document.getElementById('category-id').value = '';
        this.modal.show();
    },

    openEdit(id) {
        const cat = this.items.find(c => c.id === id);
        if (!cat) return;
        this.editingId = id;
        document.getElementById('categoryModalTitle').innerHTML =
            '<i class="bi bi-pencil"></i> Editar Categoría';
        document.getElementById('category-id').value = cat.id;
        document.getElementById('category-name').value = cat.name;
        document.getElementById('category-description').value = cat.description || '';
        document.getElementById('category-active').checked = cat.is_active;
        this.modal.show();
    },

    async save(event) {
        event.preventDefault();
        const payload = {
            name: document.getElementById('category-name').value.trim(),
            description: document.getElementById('category-description').value.trim(),
            is_active: document.getElementById('category-active').checked,
        };

        try {
            if (this.editingId) {
                await API.patch(`/api/categories/${this.editingId}/`, payload);
                showFlash('Categoría actualizada.', 'success');
            } else {
                await API.post('/api/categories/', payload);
                showFlash('Categoría creada.', 'success');
            }
            this.modal.hide();
            await this.load();
        } catch (e) {
            const err = e.data?.name?.[0] || e.data?.detail || 'Error al guardar.';
            showFlash(err, 'danger');
        }
    },

    async remove(id) {
        const cat = this.items.find(c => c.id === id);
        if (!confirm(`¿Eliminar la categoría "${cat.name}"?\n\nSi tiene productos asociados, la operación será rechazada por integridad referencial.`)) return;

        try {
            await API.delete(`/api/categories/${id}/`);
            showFlash('Categoría eliminada.', 'info');
            await this.load();
        } catch (e) {
            const msg = e.data?.detail ||
                'No se puede eliminar: tiene productos asociados o el backend lo rechazó.';
            showFlash(msg, 'danger');
        }
    },
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('categories-tbody')) {
        CategoriesCRUD.init();
    }
});