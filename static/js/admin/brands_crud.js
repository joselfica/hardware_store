/**
 * ============================================================================
 * CRUD DE MARCAS - Panel de Administración
 * ============================================================================
 * Permite al ADMIN gestionar marcas con paginación, búsqueda y CRUD completo.
 * ============================================================================
 */

const BrandsCRUD = {
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
        this.modal = new bootstrap.Modal(document.getElementById('brandModal'));
        await this.load();
    },

    // ========================================================================
    // CARGA DE DATOS
    // ========================================================================

    /**
     * Construye la URL con filtros y paginación.
     */
    buildUrl() {
        const params = new URLSearchParams();
        if (this.searchTerm) params.append('search', this.searchTerm);
        if (this.currentPage > 1) params.append('page', this.currentPage);
        const qs = params.toString();
        return '/api/brands/' + (qs ? '?' + qs : '');
    },

    /**
     * Carga la lista de marcas con paginación.
     */
    async load() {
        const tbody = document.getElementById('brands-tbody');
        if (!tbody) return;

        tbody.innerHTML = `
            <tr><td colspan="6" class="text-center py-4">
                <div class="spinner-border spinner-border-sm text-primary"></div>
                Cargando marcas...
            </td></tr>`;

        try {
            const data = await API.get(this.buildUrl());
            this.items = data.results || data;
            this.render();
            this.renderPagination(data);
        } catch (e) {
            tbody.innerHTML = `
                <tr><td colspan="6" class="text-center text-danger py-4">
                    Error al cargar marcas
                </td></tr>`;
        }
    },

    // ========================================================================
    // RENDERIZADO
    // ========================================================================

    render() {
        const tbody = document.getElementById('brands-tbody');
        if (!tbody) return;

        if (this.items.length === 0) {
            tbody.innerHTML = `
                <tr><td colspan="6" class="text-center text-muted py-4">
                    No hay marcas registradas
                </td></tr>`;
            return;
        }

        tbody.innerHTML = this.items.map(b => `
            <tr>
                <td><code class="small">#${b.id}</code></td>
                <td class="fw-semibold">${escapeHtml(b.name)}</td>
                <td class="text-muted small">${escapeHtml(b.slug)}</td>
                <td>
                    <span class="badge text-bg-${b.is_active ? 'success' : 'secondary'}">
                        ${b.is_active ? 'Activa' : 'Inactiva'}
                    </span>
                </td>
                <td>
                    <span class="badge text-bg-info">${b.products_count || 0}</span>
                </td>
                <td class="text-end">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary"
                                onclick="BrandsCRUD.openEdit(${b.id})" title="Editar">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger"
                                onclick="BrandsCRUD.remove(${b.id})" title="Eliminar">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    },

    renderPagination(data) {
        const container = document.getElementById('brands-pagination');
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
                           onclick="BrandsCRUD.goPage(${this.currentPage - 1}); return false;">
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
                           onclick="BrandsCRUD.goPage(${this.currentPage + 1}); return false;">
                            <i class="bi bi-chevron-right"></i>
                        </a>
                    </li>
                </ul>
            </nav>`;
    },

    goPage(page) {
        if (page < 1) return;
        this.currentPage = page;
        this.load();
    },

    // ========================================================================
    // CRUD
    // ========================================================================

    openCreate() {
        this.editingId = null;
        document.getElementById('brandModalTitle').innerHTML =
            '<i class="bi bi-plus-circle"></i> Nueva Marca';
        document.getElementById('brand-form').reset();
        document.getElementById('brand-id').value = '';
        document.getElementById('brand-active').checked = true;
        this.modal.show();
    },

    openEdit(id) {
        const b = this.items.find(x => x.id === id);
        if (!b) return;

        this.editingId = id;
        document.getElementById('brandModalTitle').innerHTML =
            '<i class="bi bi-pencil"></i> Editar Marca';
        document.getElementById('brand-id').value = b.id;
        document.getElementById('brand-name').value = b.name;
        document.getElementById('brand-description').value = b.description || '';
        document.getElementById('brand-active').checked = b.is_active;
        this.modal.show();
    },

    async save(event) {
        event.preventDefault();

        const payload = {
            name: document.getElementById('brand-name').value.trim(),
            description: document.getElementById('brand-description').value.trim(),
            is_active: document.getElementById('brand-active').checked,
        };

        if (!payload.name) {
            showFlash('El nombre de la marca es obligatorio.', 'warning');
            return;
        }

        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';

        try {
            if (this.editingId) {
                await API.patch(`/api/brands/${this.editingId}/`, payload);
                showFlash('Marca actualizada.', 'success');
            } else {
                await API.post('/api/brands/', payload);
                showFlash('Marca creada.', 'success');
            }
            this.modal.hide();
            await this.load();
        } catch (e) {
            let msg = 'Error al guardar la marca.';
            if (e.data) {
                if (typeof e.data === 'string') msg = e.data;
                else if (e.data.name) msg = Array.isArray(e.data.name) ? e.data.name[0] : e.data.name;
                else if (e.data.detail) msg = e.data.detail;
                else {
                    const firstKey = Object.keys(e.data)[0];
                    if (firstKey) {
                        const val = e.data[firstKey];
                        msg = Array.isArray(val) ? val[0] : val;
                    }
                }
            }
            showFlash(msg, 'danger');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
        }
    },

    async remove(id) {
        const b = this.items.find(x => x.id === id);
        if (!b) return;
        if (!confirm(`¿Eliminar la marca "${b.name}"?`)) return;

        try {
            await API.delete(`/api/brands/${id}/`);
            showFlash('Marca eliminada.', 'info');
            await this.load();
        } catch (e) {
            const msg = e.data?.detail
                || 'No se puede eliminar: tiene productos asociados.';
            showFlash(msg, 'danger');
        }
    },

    // ========================================================================
    // BÚSQUEDA CON DEBOUNCE
    // ========================================================================

    debouncedSearch() {
        clearTimeout(this.searchTimer);
        this.searchTimer = setTimeout(() => {
            const input = document.getElementById('brand-search');
            this.searchTerm = input ? input.value.trim() : '';
            this.currentPage = 1;
            this.load();
        }, 400);
    },
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('brands-tbody')) BrandsCRUD.init();
});