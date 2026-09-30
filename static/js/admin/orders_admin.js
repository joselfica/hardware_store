/**
 * ============================================================================
 * GESTIÓN DE ÓRDENES - Panel de Administración
 * ============================================================================
 * Permite al admin:
 *   - Ver todas las órdenes del sistema.
 *   - Filtrar por estado.
 *   - Cambiar estado (PAGADO, ENTREGADO, CANCELADO).
 *   - Ver detalle de cada orden.
 *
 * El backend valida las transiciones y repone stock si aplica.
 * ============================================================================
 */

const OrdersAdmin = {
    items: [],
    filterStatus: '',

    async init() {
        await this.load();
    },

    async load() {
        const tbody = document.getElementById('orders-tbody');
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4">
            <div class="spinner-border spinner-border-sm text-primary"></div> Cargando...
        </td></tr>`;
        try {
            let url = '/api/orders/';
            if (this.filterStatus) url += `?status=${this.filterStatus}`;
            const data = await API.get(url);
            this.items = data.results || data;
            this.render();
        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-danger py-4">Error</td></tr>`;
        }
    },

    render() {
        const tbody = document.getElementById('orders-tbody');
        if (this.items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-4">No hay órdenes</td></tr>`;
            return;
        }
        const statusColors = {
            'PENDIENTE': 'warning', 'PAGADO': 'success',
            'ENTREGADO': 'primary', 'CANCELADO': 'danger',
        };

        tbody.innerHTML = this.items.map(o => `
            <tr>
                <td><code class="small">${o.order_number.slice(0, 8)}...</code></td>
                <td>${escapeHtml(o.username)}</td>
                <td class="text-center">${o.total_items}</td>
                <td class="text-end fw-semibold">${formatCLP(o.total)}</td>
                <td>
                    <span class="badge bg-${statusColors[o.status] || 'secondary'}">
                        ${o.status_display}
                    </span>
                </td>
                <td class="text-muted small">${new Date(o.created_at).toLocaleDateString('es-CL')}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-1"
                            onclick="OrdersAdmin.showDetail('${o.order_number}')">
                        <i class="bi bi-eye"></i>
                    </button>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-secondary dropdown-toggle"
                                data-bs-toggle="dropdown">
                            <i class="bi bi-arrow-repeat"></i> Estado
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end">
                            ${o.status === 'PENDIENTE' ? `
                                <li><a class="dropdown-item" href="#" onclick="OrdersAdmin.changeStatus('${o.order_number}', 'PAGADO', event)">
                                    <i class="bi bi-check-circle text-success"></i> Marcar PAGADO
                                </a></li>` : ''}
                            ${o.status === 'PAGADO' ? `
                                <li><a class="dropdown-item" href="#" onclick="OrdersAdmin.changeStatus('${o.order_number}', 'ENTREGADO', event)">
                                    <i class="bi bi-box-seam text-primary"></i> Marcar ENTREGADO
                                </a></li>` : ''}
                            ${(o.status === 'PENDIENTE' || o.status === 'PAGADO') ? `
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item text-danger" href="#" onclick="OrdersAdmin.changeStatus('${o.order_number}', 'CANCELADO', event)">
                                    <i class="bi bi-x-circle"></i> Cancelar (repone stock)
                                </a></li>` : ''}
                        </ul>
                    </div>
                </td>
            </tr>
        `).join('');
    },

    async changeStatus(orderNumber, newStatus, event) {
        event.preventDefault();
        const confirmMsg = newStatus === 'CANCELADO'
            ? '¿Cancelar esta orden? Si estaba PAGADA, se repondrá el stock.'
            : `¿Cambiar la orden a ${newStatus}?`;
        if (!confirm(confirmMsg)) return;

        try {
            await API.patch(`/api/orders/${orderNumber}/status/`, { status: newStatus });
            showFlash(`Orden actualizada a ${newStatus}.`, 'success');
            await this.load();
        } catch (e) {
            const msg = e.data?.stock?.[0] || e.data?.status?.[0] || 'Error al cambiar estado.';
            showFlash(msg, 'danger');
        }
    },

    async showDetail(orderNumber) {
        try {
            const o = await API.get(`/api/orders/${orderNumber}/`);
            const itemsHtml = o.items.map(i => `
                <tr>
                    <td>${escapeHtml(i.product_name)}</td>
                    <td class="text-center">${i.quantity}</td>
                    <td class="text-end">${formatCLP(i.unit_price)}</td>
                    <td class="text-end">${formatCLP(i.subtotal)}</td>
                </tr>`).join('');

            document.getElementById('order-detail-body').innerHTML = `
                <div class="mb-3">
                    <div><strong>Orden:</strong> <code>${o.order_number}</code></div>
                    <div><strong>Cliente:</strong> ${escapeHtml(o.username)}</div>
                    <div><strong>Estado:</strong> ${o.status_display}</div>
                    <div><strong>Fecha:</strong> ${new Date(o.created_at).toLocaleString('es-CL')}</div>
                    ${o.paid_at ? `<div><strong>Pagado:</strong> ${new Date(o.paid_at).toLocaleString('es-CL')}</div>` : ''}
                    ${o.cancelled_at ? `<div><strong>Cancelado:</strong> ${new Date(o.cancelled_at).toLocaleString('es-CL')}</div>` : ''}
                </div>
                <table class="table table-sm">
                    <thead><tr><th>Producto</th><th class="text-center">Cant.</th><th class="text-end">Precio</th><th class="text-end">Subtotal</th></tr></thead>
                    <tbody>${itemsHtml}</tbody>
                    <tfoot><tr><th colspan="3" class="text-end">Total:</th><th class="text-end">${formatCLP(o.total)}</th></tr></tfoot>
                </table>`;
            new bootstrap.Modal(document.getElementById('orderDetailModal')).show();
        } catch (e) {
            showFlash('Error al cargar detalle.', 'danger');
        }
    },

    setFilter(status, event) {
        if (event) event.preventDefault();
        this.filterStatus = status;
        document.querySelectorAll('#order-filters .btn').forEach(b => b.classList.remove('active'));
        event?.target.closest('.btn')?.classList.add('active');
        this.load();
    },
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('orders-tbody')) OrdersAdmin.init();
});