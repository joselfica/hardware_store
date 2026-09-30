/**
 * ============================================================================
 * CARRO DE COMPRAS - Visualización y edición
 * ============================================================================
 * Consume /api/cart/ y permite modificar cantidades y eliminar ítems.
 * Persiste en PostgreSQL (no en localStorage): al recargar la página,
 * los ítems siguen ahí.
 *
 * Notas de estilo:
 *   - Usa clases btn-hs-* en lugar de btn-* de Bootstrap para mantener
 *     la identidad visual del proyecto y compatibilidad con el modo oscuro.
 *   - La fila con stock insuficiente usa .row-warning (custom) en lugar de
 *     .table-warning (que se ve mal en dark mode).
 * ============================================================================
 */

const Cart = {
    async load() {
        const container = document.getElementById('cart-container');
        if (!API.isAuthenticated()) {
            container.innerHTML = `
                <div class="alert alert-warning text-center">
                    <i class="bi bi-exclamation-triangle"></i>
                    Debes <a href="/login/" class="alert-link">iniciar sesión</a> para ver tu carro.
                </div>`;
            return;
        }
        try {
            const cart = await API.get('/api/cart/');
            this.render(cart);
        } catch (e) {
            container.innerHTML = `<div class="alert alert-danger">Error al cargar el carro.</div>`;
        }
    },

    render(cart) {
        const container = document.getElementById('cart-container');

        if (!cart.items || cart.items.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-cart-x display-1 text-muted"></i>
                    <h4 class="mt-3">Tu carro está vacío</h4>
                    <p class="text-muted">Agrega productos desde el catálogo.</p>
                    <a href="/" class="btn btn-hs-primary">
                        <i class="bi bi-shop"></i> Ir al catálogo
                    </a>
                </div>`;
            return;
        }

        // ⚠️ Detectar ítems cuyo producto ya no tiene stock suficiente
        const itemsWithIssues = cart.items.filter(item => item.quantity > item.product_stock);
        const hasIssues = itemsWithIssues.length > 0;

        container.innerHTML = `
            ${hasIssues ? `
                <div class="alert alert-warning d-flex align-items-center mb-3">
                    <i class="bi bi-exclamation-triangle-fill fs-4 me-3"></i>
                    <div>
                        <strong>Algunos productos ya no tienen stock suficiente.</strong>
                        <p class="mb-0 small">
                            Ajusta las cantidades antes de continuar con el checkout.
                        </p>
                    </div>
                </div>
            ` : ''}

            <div class="row g-4">
                <div class="col-lg-8">
                    <div class="card shadow-sm border-0">
                        <div class="card-body p-0">
                            <table class="table table-hover align-middle mb-0">
                                <thead>
                                    <tr>
                                        <th>Producto</th>
                                        <th class="text-center" style="width:130px;">Cantidad</th>
                                        <th class="text-end">Precio</th>
                                        <th class="text-end">Subtotal</th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${cart.items.map(item => {
                                        const insufficient = item.quantity > item.product_stock;
                                        return `
                                            <tr class="${insufficient ? 'row-warning' : ''}">
                                                <td>
                                                    <div class="fw-bold">${escapeHtml(item.product_name)}</div>
                                                    <small class="text-muted">SKU: ${escapeHtml(item.product_sku)}</small>
                                                    ${insufficient ? `
                                                        <div class="small text-danger mt-1">
                                                            <i class="bi bi-exclamation-circle"></i>
                                                            Solo quedan ${item.product_stock} unidades
                                                        </div>
                                                    ` : ''}
                                                </td>
                                                <td class="text-center">
                                                    <div class="input-group input-group-sm">
                                                        <button class="btn btn-outline-secondary"
                                                                onclick="Cart.updateQty(${item.id}, ${item.quantity - 1})">−</button>
                                                        <input type="text" class="form-control text-center"
                                                               value="${item.quantity}" readonly>
                                                        <button class="btn btn-outline-secondary"
                                                                onclick="Cart.updateQty(${item.id}, ${item.quantity + 1})"
                                                                ${item.quantity >= item.product_stock ? 'disabled' : ''}>+</button>
                                                    </div>
                                                </td>
                                                <td class="text-end">${formatCLP(item.product_price)}</td>
                                                <td class="text-end fw-bold">${formatCLP(item.subtotal)}</td>
                                                <td class="text-end">
                                                    <button class="btn btn-sm btn-outline-danger"
                                                            onclick="Cart.removeItem(${item.id})">
                                                        <i class="bi bi-trash"></i>
                                                    </button>
                                                </td>
                                            </tr>
                                        `;
                                    }).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="mt-3 d-flex justify-content-between">
                        <a href="/" class="btn btn-outline-secondary">
                            <i class="bi bi-arrow-left"></i> Seguir comprando
                        </a>
                        <button class="btn btn-outline-danger" onclick="Cart.clear()">
                            <i class="bi bi-trash"></i> Vaciar carro
                        </button>
                    </div>
                </div>

                <div class="col-lg-4">
                    <div class="card shadow-sm border-0">
                        <div class="card-header fw-bold">
                            <i class="bi bi-receipt"></i> Resumen
                        </div>
                        <div class="card-body">
                            <div class="d-flex justify-content-between mb-2">
                                <span>Ítems totales:</span>
                                <strong>${cart.total_items}</strong>
                            </div>
                            <hr>
                            <div class="d-flex justify-content-between mb-3">
                                <span class="fs-5">Total:</span>
                                <span class="fs-4 fw-bold text-primary">${formatCLP(cart.total_price)}</span>
                            </div>
                            <button class="btn btn-hs-success w-100"
                                    onclick="Cart.checkout()"
                                    ${hasIssues ? 'disabled' : ''}>
                                <i class="bi bi-credit-card"></i>
                                ${hasIssues ? 'Ajusta tu carro para continuar' : 'Proceder al checkout'}
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;
    },

    async updateQty(itemId, newQty) {
        if (newQty < 1) return;
        try {
            await API.patch(`/api/cart/items/${itemId}/`, { quantity: newQty });
            this.load();
            Auth.updateCartBadge();
        } catch (e) {
            // DRF puede devolver string o lista según cómo se lance el error
            const pick = v => (Array.isArray(v) ? v[0] : v);
            const msg = pick(e.data?.quantity)
                || pick(e.data?.product)
                || pick(e.data?.item)
                || e.data?.detail
                || 'Error al actualizar.';
            showFlash(msg, 'danger');
            // Recargar para sincronizar con el backend
            this.load();
            Auth.updateCartBadge();
        }
    },

    async removeItem(itemId) {
        if (!confirm('¿Eliminar este producto del carro?')) return;
        try {
            await API.delete(`/api/cart/items/${itemId}/delete/`);
            showFlash('Producto eliminado.', 'info');
            this.load();
            Auth.updateCartBadge();
        } catch (e) {
            showFlash('Error al eliminar.', 'danger');
        }
    },

    async clear() {
        if (!confirm('¿Vaciar todo el carro?')) return;
        try {
            await API.delete('/api/cart/clear/');
            showFlash('Carro vaciado.', 'info');
            this.load();
            Auth.updateCartBadge();
        } catch (e) {
            showFlash('Error al vaciar.', 'danger');
        }
    },

    async checkout() {
        if (!confirm('¿Confirmar tu pedido? Se generará una orden pendiente de pago.')) return;
        try {
            const data = await API.post('/api/orders/checkout/');
            showFlash('Orden creada. Procede al pago.', 'success');
            Auth.updateCartBadge();
            setTimeout(() => window.location.href = '/mis-ordenes/', 1000);
        } catch (e) {
            const msg = e.data?.stock?.[0] || e.data?.cart?.[0] || 'Error en el checkout.';
            showFlash(msg, 'danger');
        }
    },
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('cart-container')) Cart.load();
});