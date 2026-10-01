/**
 * ============================================================================
 * CRUD DE PRODUCTOS - Panel de Administración
 * ============================================================================
 * CRUD completo de productos con soporte para:
 *   - Listado paginado con búsqueda.
 *   - Creación/edición con formulario modal.
 *   - Subida y actualización de imágenes (multipart/form-data).
 *   - Eliminación con confirmación.
 *
 * IMPORTANTE: el CRUD se hace 100% desde el frontend, sin usar el admin
 * nativo de Django. Se comunica exclusivamente con la API REST.
 * ============================================================================
 */

const ProductsCRUD = {
    items: [],
    categories: [],
    brands: [],
    editingId: null,
    modal: null,
    currentPage: 1,
    searchTerm: '',
    searchTimer: null,
    clearImageFlag: false,   // Bandera: el usuario quiere quitar la imagen

    // ========================================================================
    // INICIALIZACIÓN
    // ========================================================================

    async init() {
        this.modal = new bootstrap.Modal(document.getElementById('productModal'));

        // Resetear la bandera al cerrar el modal
        document.getElementById('productModal').addEventListener('hidden.bs.modal', () => {
            this.clearImageFlag = false;
        });

        await this.loadSelects();
        await this.load();
    },

    // ========================================================================
    // CARGA DE SELECTS (categorías y marcas)
    // ========================================================================

    async loadSelects() {
        try {
            const [cats, brands] = await Promise.all([
                API.get('/api/categories/?is_active=true&page_size=100'),
                API.get('/api/brands/?is_active=true&page_size=100'),
            ]);

            this.categories = cats.results || cats;
            this.brands = brands.results || brands;

            const catSelect = document.getElementById('product-category');
            const brandSelect = document.getElementById('product-brand');

            catSelect.innerHTML = '<option value="">Selecciona categoría...</option>' +
                this.categories.map(c =>
                    `<option value="${c.id}">${escapeHtml(c.name)}</option>`
                ).join('');

            brandSelect.innerHTML = '<option value="">Selecciona marca...</option>' +
                this.brands.map(b =>
                    `<option value="${b.id}">${escapeHtml(b.name)}</option>`
                ).join('');
        } catch (e) {
            showFlash('Error al cargar categorías/marcas.', 'danger');
        }
    },

    // ========================================================================
    // CARGA DE PRODUCTOS
    // ========================================================================

    buildUrl() {
        const params = new URLSearchParams();
        if (this.searchTerm) params.append('search', this.searchTerm);
        if (this.currentPage > 1) params.append('page', this.currentPage);
        // Traer todos los productos (incluso sin stock) para el admin
        params.append('include_out_of_stock', 'true');
        params.append('page_size', '20');

        const qs = params.toString();
        return '/api/products/' + (qs ? '?' + qs : '');
    },

    async load() {
        const tbody = document.getElementById('products-tbody');
        if (!tbody) return;

        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <div class="spinner-border spinner-border-sm text-primary"></div>
                    Cargando productos...
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
                        Error al cargar productos
                    </td>
                </tr>`;
        }
    },

    // ========================================================================
    // RENDERIZADO DE LA TABLA
    // ========================================================================

    render() {
        const tbody = document.getElementById('products-tbody');
        if (!tbody) return;

        if (this.items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        No hay productos
                    </td>
                </tr>`;
            return;
        }

        tbody.innerHTML = this.items.map(p => {
            // Badge de stock con color según nivel
            let stockBadge = 'text-bg-success';
            if (p.stock === 0) stockBadge = 'text-bg-danger';
            else if (p.stock <= 5) stockBadge = 'text-bg-warning';

            // Thumbnail de imagen o ícono placeholder
            const imageThumb = p.image
                ? `<img src="${p.image}" alt="${escapeHtml(p.name)}"
                        style="width: 40px; height: 40px; object-fit: cover;
                               border-radius: 6px;">`
                : `<div class="d-flex align-items-center justify-content-center"
                        style="width: 40px; height: 40px; border-radius: 6px;
                               background: var(--hs-surface-2);">
                       <i class="bi bi-cpu text-muted"></i>
                   </div>`;

            return `
                <tr>
                    <td>${imageThumb}</td>
                    <td>
                        <code class="small">${escapeHtml(p.sku)}</code>
                    </td>
                    <td>
                        <div class="fw-semibold">${escapeHtml(p.name)}</div>
                        <small class="text-muted">
                            ${escapeHtml(p.brand_name || '')} ·
                            ${escapeHtml(p.category_name || '')}
                        </small>
                    </td>
                    <td class="text-end fw-semibold">${formatCLP(p.price)}</td>
                    <td class="text-center">
                        <span class="badge ${stockBadge}">${p.stock}</span>
                    </td>
                    <td>
                        <span class="badge text-bg-${p.is_active ? 'success' : 'secondary'}">
                            ${p.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                    </td>
                    <td class="text-end">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary"
                                    onclick="ProductsCRUD.openEdit(${p.id})"
                                    title="Editar producto">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-outline-danger"
                                    onclick="ProductsCRUD.remove(${p.id})"
                                    title="Eliminar producto">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>`;
        }).join('');
    },

    renderPagination(data) {
        const container = document.getElementById('products-pagination');
        if (!container) return;

        if (!data.next && !data.previous) {
            container.innerHTML = '';
            return;
        }

        const total = data.count || 0;
        const pageSize = 20;
        const totalPages = Math.ceil(total / pageSize);

        container.innerHTML = `
            <nav>
                <ul class="pagination justify-content-center mb-0">
                    <li class="page-item ${!data.previous ? 'disabled' : ''}">
                        <a class="page-link" href="#"
                           onclick="ProductsCRUD.goPage(${this.currentPage - 1}); return false;">
                            <i class="bi bi-chevron-left"></i>
                        </a>
                    </li>
                    <li class="page-item active">
                        <span class="page-link">Página ${this.currentPage} de ${totalPages}</span>
                    </li>
                    <li class="page-item ${!data.next ? 'disabled' : ''}">
                        <a class="page-link" href="#"
                           onclick="ProductsCRUD.goPage(${this.currentPage + 1}); return false;">
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

    debouncedSearch() {
        clearTimeout(this.searchTimer);
        this.searchTimer = setTimeout(() => {
            const input = document.getElementById('product-search');
            this.searchTerm = input ? input.value.trim() : '';
            this.currentPage = 1;
            this.load();
        }, 400);
    },

    // ========================================================================
    // CREAR / EDITAR
    // ========================================================================

    openCreate() {
        this.editingId = null;
        this.clearImageFlag = false;

        document.getElementById('productModalTitle').innerHTML =
            '<i class="bi bi-plus-circle"></i> Nuevo Producto';
        document.getElementById('product-form').reset();
        document.getElementById('product-id').value = '';
        document.getElementById('product-sku').disabled = false;
        document.getElementById('product-image-preview-container').style.display = 'none';

        this.modal.show();
    },

    async openEdit(id) {
        try {
            const p = await API.get(`/api/products/${id}/`);

            this.editingId = id;
            this.clearImageFlag = false;

            document.getElementById('productModalTitle').innerHTML =
                '<i class="bi bi-pencil"></i> Editar Producto';
            document.getElementById('product-id').value = p.id;
            document.getElementById('product-sku').value = p.sku;
            document.getElementById('product-sku').disabled = true;
            document.getElementById('product-name').value = p.name;
            document.getElementById('product-description').value = p.description || '';
            document.getElementById('product-category').value = p.category.id;
            document.getElementById('product-brand').value = p.brand.id;
            document.getElementById('product-price').value = p.price;
            document.getElementById('product-stock').value = p.stock;
            document.getElementById('product-active').checked = p.is_active;

            // Resetear input de archivo
            document.getElementById('product-image').value = '';

            // Mostrar preview si hay imagen
            const previewContainer = document.getElementById('product-image-preview-container');
            const preview = document.getElementById('product-image-preview');

            if (p.image) {
                preview.src = p.image;
                previewContainer.style.display = 'block';
            } else {
                previewContainer.style.display = 'none';
            }

            this.modal.show();
        } catch (e) {
            showFlash('Error al cargar producto.', 'danger');
        }
    },

    /**
     * Marca la imagen para eliminarla al guardar.
     */
    clearImage() {
        this.clearImageFlag = true;
        document.getElementById('product-image-preview-container').style.display = 'none';
        document.getElementById('product-image').value = '';
    },

    // ========================================================================
    // GUARDAR (con soporte de FormData para imágenes)
    // ========================================================================

    async save(event) {
        event.preventDefault();

        // --- Validaciones locales ---
        const price = parseInt(document.getElementById('product-price').value, 10);
        const stock = parseInt(document.getElementById('product-stock').value, 10);

        if (price <= 0) {
            showFlash('El precio debe ser mayor a 0.', 'warning');
            return;
        }
        if (stock < 0) {
            showFlash('El stock no puede ser negativo.', 'warning');
            return;
        }

        // --- Construir FormData (necesario para subir archivos) ---
        const formData = new FormData();

        formData.append('name', document.getElementById('product-name').value.trim());
        formData.append('description', document.getElementById('product-description').value.trim());
        formData.append('category_id', document.getElementById('product-category').value);
        formData.append('brand_id', document.getElementById('product-brand').value);
        formData.append('price', price);
        formData.append('stock', stock);
        formData.append('is_active', document.getElementById('product-active').checked);

        // SKU solo al crear
        if (!this.editingId) {
            formData.append('sku', document.getElementById('product-sku').value.trim().toUpperCase());
        }

        // --- Imagen ---
        const imageInput = document.getElementById('product-image');
        if (imageInput.files && imageInput.files[0]) {
            // Nueva imagen seleccionada
            formData.append('image', imageInput.files[0]);
        } else if (this.editingId && this.clearImageFlag) {
            // Estamos editando y el usuario quitó la imagen
            formData.append('image', '');
        }

        // --- Enviar al backend ---
        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Guardando...';

        try {
            const url = this.editingId
                ? `/api/products/${this.editingId}/`
                : '/api/products/';
            const method = this.editingId ? 'PATCH' : 'POST';

            // Pasar isFormData=true para que API.request no use JSON.stringify
            await API.request(method, url, formData, true, true);

            showFlash(
                this.editingId ? 'Producto actualizado.' : 'Producto creado.',
                'success'
            );
            this.modal.hide();
            await this.load();
        } catch (e) {
            const errs = e.data || {};
            let msg = 'Error al guardar.';

            if (typeof errs === 'string') {
                msg = errs;
            } else {
                msg = Object.entries(errs)
                    .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
                    .join(' · ') || 'Error al guardar.';
            }
            showFlash(msg, 'danger');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalHtml;
        }
    },

    // ========================================================================
    // ELIMINAR
    // ========================================================================

    async remove(id) {
        const p = this.items.find(x => x.id === id);
        if (!p) return;

        if (!confirm(`¿Eliminar el producto "${p.name}"?\n\nEsta acción no se puede deshacer.`)) {
            return;
        }

        try {
            await API.delete(`/api/products/${id}/`);
            showFlash('Producto eliminado.', 'info');
            await this.load();
        } catch (e) {
            const msg = e.data?.detail ||
                'No se puede eliminar: tiene órdenes asociadas.';
            showFlash(msg, 'danger');
        }
    },
};

// ============================================================================
// INICIALIZACIÓN
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('products-tbody')) {
        ProductsCRUD.init();
    }
});