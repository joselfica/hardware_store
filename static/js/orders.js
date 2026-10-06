/**
 * ============================================================================
 * ÓRDENES - Historial del cliente y cambio de estado
 * ============================================================================
 * Consume /api/orders/my-orders/ y permite al cliente:
 *   - Ver sus órdenes.
 *   - Pagar las órdenes PENDIENTES.
 *   - Cancelar las órdenes PENDIENTES (antes de pagar).
 *   - Ver el detalle de cada orden.
 *
 * Reglas de negocio:
 *   - El cliente puede pagar y cancelar SOLO órdenes PENDIENTES.
 *   - Una vez pagada, la cancelación requiere intervención del admin.
 *
 * Notas de estilo:
 *   - Los badges de estado usan text-bg-* para contraste automático.
 *   - Los botones usan btn-hs-* para mantener la identidad visual.
 *
 * Autor: José Fica
 * Sección: AP-N4-C2
 * Año: 2026
 * ============================================================================
 */

const Orders = {
    // ========================================================================
    // CARGA DE ÓRDENES
    // ========================================================================

    async load() {
        const container = document.getElementById('orders-container');
        if (!API.isAuthenticated()) {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <a href="/login/">Inicia sesión</a> para ver tus órdenes.
                </div>`;
            return;
        }
        try {
            const data = await API.get('/api/orders/my-orders/');
            const orders = data.results || data;
            this.render(orders);
        } catch (e) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    Error al cargar órdenes.
                </div>`;
        }
    },

    // ========================================================================
    // RENDERIZADO
    // ========================================================================

    render(orders) {
        const container = document.getElementById('orders-container');

        if (orders.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-receipt display-1 text-muted"></i>
                    <h4 class="mt-3">Aún no tienes órdenes</h4>
                    <a href="/" class="btn btn-hs-primary">Ir al catálogo</a>
                </div>`;
            return;
        }

        // Colores de Bootstrap compatibles con text-bg-* para buen contraste
        const statusColors = {
            'PENDIENTE': 'warning',
            'PAGADO': 'success',
            'ENTREGADO': 'primary',
            'CANCELADO': 'danger',
        };

        container.innerHTML = orders.map(o => {
            // Botones de acción según el estado de la orden
            let actionsHtml = '';

            if (o.status === 'PENDIENTE') {
                // PENDIENTE → puede Pagar o Cancelar
                actionsHtml = `
                    <button class="btn btn-sm btn-hs-success me-1"
                            onclick="Orders.pay('${o.order_number}')">
                        <i class="bi bi-credit-card"></i> Pagar
                    </button>
                    <button class="btn btn-sm btn-outline-danger me-1"
                            onclick="Orders.cancel('${o.order_number}')">
                        <i class="bi bi-x-circle"></i> Cancelar
                    </button>
                `;
            }
            // PAGADO, ENTREGADO, CANCELADO: solo ver (sin acciones de cambio)

            actionsHtml += `
                <button class="btn btn-sm btn-hs-outline"
                        onclick="Orders.showDetail('${o.order_number}')">
                    <i class="bi bi-eye"></i> Ver
                </button>
            `;

            return `
                <div class="card shadow-sm border-0 mb-3">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-md-3">
                                <small class="text-muted">Orden</small>
                                <div class="fw-bold">
                                    <code>${o.order_number.slice(0, 8)}...</code>
                                </div>
                                <small class="text-muted">
                                    ${new Date(o.created_at).toLocaleDateString('es-CL')}
                                </small>
                            </div>
                            <div class="col-md-3">
                                <small class="text-muted">Ítems</small>
                                <div>${o.total_items} productos</div>
                            </div>
                            <div class="col-md-3">
                                <small class="text-muted">Total</small>
                                <div class="fw-bold text-primary">${formatCLP(o.total)}</div>
                            </div>
                            <div class="col-md-3 text-end">
                                <span class="badge text-bg-${statusColors[o.status] || 'secondary'} mb-2">
                                    ${o.status_display}
                                </span>
                                <div>${actionsHtml}</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    },

    // ========================================================================
    // ACCIÓN: PAGAR
    // ========================================================================

    async pay(orderNumber) {
        if (!confirm('¿Confirmar el pago?\n\nSe descontará stock del catálogo.')) {
            return;
        }

        try {
            await API.patch(`/api/orders/${orderNumber}/status/`, {
                status: 'PAGADO',
            });
            showFlash('¡Pago confirmado! Stock descontado.', 'success');
            this.load();
        } catch (e) {
            const msg = e.data?.stock?.[0]
                || e.data?.status?.[0]
                || 'Error al pagar.';
            showFlash(msg, 'danger');
        }
    },

    // ========================================================================
    // ACCIÓN: CANCELAR (nuevo)
    // ========================================================================
    // El cliente puede cancelar SOLO sus órdenes en estado PENDIENTE.
    // Una vez pagada, la cancelación requiere intervención del admin.
    //
    // Al cancelar una orden PENDIENTE, el stock no se ve afectado porque
    // nunca se descontó (solo se descuenta al pagar).
    // ========================================================================

    async cancel(orderNumber) {
        const confirmMsg = [
            '¿Cancelar esta orden?',
            '',
            'Esta acción no se puede deshacer.',
            'Si la orden estaba pendiente, no se descontará stock.',
        ].join('\n');

        if (!confirm(confirmMsg)) return;

        try {
            await API.patch(`/api/orders/${orderNumber}/status/`, {
                status: 'CANCELADO',
            });
            showFlash('Orden cancelada correctamente.', 'success');
            this.load();
        } catch (e) {
            const msg = e.data?.status?.[0]
                || e.data?.detail
                || 'No se pudo cancelar la orden.';
            showFlash(msg, 'danger');
        }
    },

    // ========================================================================
    // ACCIÓN: VER DETALLE
    // ========================================================================

    async showDetail(orderNumber) {
        try {
            const o = await API.get(`/api/orders/${orderNumber}/`);

            const itemsHtml = o.items.map(i => `
                <tr>
                    <td>${escapeHtml(i.product_name)}</td>
                    <td class="text-center">${i.quantity}</td>
                    <td class="text-end">${formatCLP(i.unit_price)}</td>
                    <td class="text-end fw-bold">${formatCLP(i.subtotal)}</td>
                </tr>
            `).join('');

            const modal = `
                <div class="modal fade" id="orderModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    Orden <code>${o.order_number.slice(0, 8)}...</code>
                                </h5>
                                <button type="button" class="btn-close"
                                        data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <p><strong>Estado:</strong> ${o.status_display}</p>
                                <p><strong>Fecha:</strong> ${new Date(o.created_at).toLocaleString('es-CL')}</p>
                                ${o.paid_at ? `<p><strong>Pagado:</strong> ${new Date(o.paid_at).toLocaleString('es-CL')}</p>` : ''}
                                ${o.cancelled_at ? `<p><strong>Cancelado:</strong> ${new Date(o.cancelled_at).toLocaleString('es-CL')}</p>` : ''}
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th>Producto</th>
                                            <th class="text-center">Cant.</th>
                                            <th class="text-end">Precio</th>
                                            <th class="text-end">Subtotal</th>
                                        </tr>
                                    </thead>
                                    <tbody>${itemsHtml}</tbody>
                                    <tfoot>
                                        <tr>
                                            <th colspan="3" class="text-end">Total:</th>
                                            <th class="text-end">${formatCLP(o.total)}</th>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>`;

            // Elimina modal previo si existe
            document.getElementById('orderModal')?.remove();
            document.body.insertAdjacentHTML('beforeend', modal);
            new bootstrap.Modal(document.getElementById('orderModal')).show();
        } catch (e) {
            showFlash('Error al cargar detalle.', 'danger');
        }
    },
};

// ============================================================================
// INICIALIZACIÓN
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('orders-container')) Orders.load();
});