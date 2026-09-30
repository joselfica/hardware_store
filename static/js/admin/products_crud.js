/**
 * ============================================================================
 * CRUD DE PRODUCTOS - Panel de Administración
 * ============================================================================
 * CRUD completo de productos con:
 *   - Listado paginado con búsqueda.
 *   - Modal de creación/edición con todos los campos (incluye brand_id y
 *     category_id como selects dinámicos).
 *   - Validaciones locales antes de enviar al backend.
 *   - Eliminación con confirmación.
 *   - Badges visuales de stock (verde/amarillo/rojo).
 * ============================================================================
 */

const ProductsCRUD = {
    items: [],
    categories: [],
    brands: [],
    editingId: null,
    modal: null,

    async init() {
        this.modal = new bootstrap.Modal(document.getElementById('productModal'));
        await this.loadSelects();
        await this.load();
    },

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

    async load() {
        const tbody = document.getElementById('products-tbody');
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4">
            <div class="spinner-border spinner-border-sm text-primary"></div> Cargando...
        </td></tr>`;
        try {
            const data = await API.get('/api/products/');
            this.items = data.results || data;
            this.render();
        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Error</td></tr>`;
        }
    },

    render() {
        const tbody = document.getElementById('products-tbody');
        if (this.items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">No hay productos</td></tr>`;
            return;
        }
        tbody.innerHTML = this.items.map(p => {
            const stockBadge = p.stock === 0
                ? 'bg-danger'
                : (p.stock <= 5 ? 'bg-warning text-dark' : 'bg-success');
            return `
                <tr>
                    <td><code class="small">${escapeHtml(p.sku)}</code></td>
                    <td>
                        <div class="fw-semibold">${escapeHtml(p.name)}</div>
                        <small class="text-muted">${escapeHtml(p.brand_name || '')} · ${escapeHtml(p.category_name || '')}</small>
                    </td>
                    <td class="text-end fw-semibold">${formatCLP(p.price)}</td>
                    <td class="text-center"><span class="badge ${stockBadge}">${p.stock}</span></td>
                    <td>
                        <span class="badge bg-${p.is_active ? 'success' : 'secondary'}">
                            ${p.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                    </td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="ProductsCRUD.openEdit(${p.id})">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="ProductsCRUD.remove(${p.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>`;
        }).join('');
    },

    openCreate() {
        this.editingId = null;
        document.getElementById('productModalTitle').innerHTML = '<i class="bi bi-plus-circle"></i> Nuevo Producto';
        document.getElementById('product-form').reset();
        document.getElementById('product-id').value = '';
        this.modal.show();
    },

    async openEdit(id) {
        try {
            const p = await API.get(`/api/products/${id}/`);
            this.editingId = id;
            document.getElementById('productModalTitle').innerHTML = '<i class="bi bi-pencil"></i> Editar Producto';
            document.getElementById('product-id').value = p.id;
            document.getElementById('product-sku').value = p.sku;
            document.getElementById('product-name').value = p.name;
            document.getElementById('product-description').value = p.description || '';
            document.getElementById('product-category').value = p.category.id;
            document.getElementById('product-brand').value = p.brand.id;
            document.getElementById('product-price').value = p.price;
            document.getElementById('product-stock').value = p.stock;
            document.getElementById('product-active').checked = p.is_active;
            this.modal.show();
        } catch (e) {
            showFlash('Error al cargar producto.', 'danger');
        }
    },

async save(event) {
    event.preventDefault();

    const price = parseInt(document.getElementById('product-price').value, 10);
    const stock = parseInt(document.getElementById('product-stock').value, 10);

    if (price < 0) {
        showFlash('El precio no puede ser negativo.', 'warning');
        return;
    }
    if (stock < 0) {
        showFlash('El stock no puede ser negativo.', 'warning');
        return;
    }

    const payload = {
        sku: document.getElementById('product-sku').value.trim().toUpperCase(),
        name: document.getElementById('product-name').value.trim(),
        description: document.getElementById('product-description').value.trim(),
        category_id: parseInt(document.getElementById('product-category').value, 10),
        brand_id: parseInt(document.getElementById('product-brand').value, 10),
        price: price,
        stock: stock,
        is_active: document.getElementById('product-active').checked,
    };

        try {
            if (this.editingId) {
                // En edición no enviamos el SKU (read-only tras creación)
                delete payload.sku;
                await API.patch(`/api/products/${this.editingId}/`, payload);
                showFlash('Producto actualizado.', 'success');
            } else {
                await API.post('/api/products/', payload);
                showFlash('Producto creado.', 'success');
            }
            this.modal.hide();
            await this.load();
        } catch (e) {
            const errs = e.data || {};
            const msg = Object.entries(errs)
                .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
                .join(' · ') || 'Error al guardar.';
            showFlash(msg, 'danger');
        }
    },

    async remove(id) {
        const p = this.items.find(x => x.id === id);
        if (!confirm(`¿Eliminar el producto "${p.name}"?`)) return;
        try {
            await API.delete(`/api/products/${id}/`);
            showFlash('Producto eliminado.', 'info');
            await this.load();
        } catch (e) {
            showFlash('No se puede eliminar: tiene órdenes asociadas.', 'danger');
        }
    },
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('products-tbody')) ProductsCRUD.init();
});