/**
 * ============================================================================
 * CATÁLOGO - Listado, filtros, búsqueda, chips y detalle de producto
 * ============================================================================
 * Consume /api/products/, /api/categories/ y /api/brands/.
 *
 * Características:
 *   - Chips de categorías con conteo de productos.
 *   - Filtros por categoría, marca, precio, stock y búsqueda.
 *   - Buscador del hero sincronizado con el filtro lateral.
 *   - Skeleton loaders durante la carga.
 *   - Contador de resultados actualizado dinámicamente.
 *   - Paginación con navegación y scroll suave.
 *   - Filtro defensivo: oculta productos sin stock al público.
 *   - Sincronización bidireccional entre chips y filtro lateral.
 * ============================================================================
 */

const Catalog = {
    // ========================================================================
    // ESTADO
    // ========================================================================

    filters: {
        search: '',
        category: '',
        brand: '',
        price_min: '',
        price_max: '',
        in_stock: false,
        ordering: '-created_at',
        page: 1,
    },

    // ========================================================================
    // CARGA DE FILTROS Y CHIPS
    // ========================================================================

    /**
     * Carga categorías y marcas desde la API, puebla los selects laterales
     * y renderiza los chips de categorías bajo el hero.
     */
    async loadFilterOptions() {
        try {
            const [cats, brands] = await Promise.all([
                API.get('/api/categories/?is_active=true'),
                API.get('/api/brands/?is_active=true'),
            ]);

            const categories = cats.results || cats;
            const brandList = brands.results || brands;

            const catSelect = document.getElementById('filter-category');
            const brandSelect = document.getElementById('filter-brand');

            // Poblar selects laterales
            categories.forEach(c => {
                catSelect.innerHTML += `<option value="${c.id}">${escapeHtml(c.name)}</option>`;
            });
            brandList.forEach(b => {
                brandSelect.innerHTML += `<option value="${b.id}">${escapeHtml(b.name)}</option>`;
            });

            // Renderizar chips de categorías
            this.renderCategoryChips(categories);
        } catch (e) {
            console.error('Error cargando filtros:', e);
        }
    },

    /**
     * Renderiza los chips de categorías debajo del hero.
     * Cada chip filtra el catálogo al hacer clic.
     *
     * @param {Array} cats - Lista de categorías desde la API.
     */
    renderCategoryChips(cats) {
        const box = document.getElementById('category-chips');
        if (!box) return;

        box.innerHTML = `
            <button type="button" class="chip active" data-id=""
                    onclick="Catalog.setCategory('')">
                <i class="bi bi-grid-3x3-gap-fill"></i> Todas
            </button>
            ${cats.map(c => `
                <button type="button" class="chip" data-id="${c.id}"
                        onclick="Catalog.setCategory('${c.id}')">
                    ${escapeHtml(c.name)}
                    ${c.products_count != null
                        ? `<span class="count">${c.products_count}</span>`
                        : ''}
                </button>`).join('')}
        `;
    },

    /**
     * Sincroniza el chip activo con el filtro de categoría actual.
     */
    syncChips() {
        document.querySelectorAll('#category-chips .chip').forEach(ch => {
            const matches = ch.dataset.id === String(this.filters.category || '');
            ch.classList.toggle('active', matches);
        });
    },

    /**
     * Establece la categoría desde un chip, sincroniza el select lateral
     * y aplica los filtros.
     *
     * @param {string} id - ID de la categoría ('' = todas).
     */
    setCategory(id) {
        const select = document.getElementById('filter-category');
        if (select) select.value = id;

        this.filters.category = id || '';
        this.filters.page = 1;

        this.syncChips();
        this.loadProducts();
    },

    // ========================================================================
    // CONSTRUCCIÓN DE QUERY
    // ========================================================================

    /**
     * Construye la query string a partir de los filtros activos.
     * Omite valores vacíos, false o null.
     */
    buildQuery() {
        const params = new URLSearchParams();
        for (const [key, val] of Object.entries(this.filters)) {
            if (val !== '' && val !== false && val !== null) {
                params.append(key, val);
            }
        }
        return params.toString();
    },

    // ========================================================================
    // CARGA DE PRODUCTOS
    // ========================================================================

    /**
     * Carga los productos desde la API aplicando los filtros.
     * Muestra skeleton loaders durante la carga y actualiza el contador.
     */
    async loadProducts() {
        const grid = document.getElementById('products-grid');
        const count = document.getElementById('results-count');

        if (!grid) return;

        // --- Estado de carga: skeletons ---
        if (count) count.textContent = 'Cargando productos...';
        grid.innerHTML = Array.from({ length: 8 }, () => `
            <div class="col-6 col-md-4 col-xxl-3">
                <div class="skeleton skeleton-card"></div>
            </div>`).join('');

        try {
            const data = await API.get(`/api/products/?${this.buildQuery()}`);
            const products = data.results || data;

            this.renderProducts(products);
            this.renderPagination(data);

            // --- Actualizar contador ---
            if (count) {
                const total = data.count ?? products.length;
                count.textContent = total === 1
                    ? '1 producto encontrado'
                    : `${total} productos encontrados`;
            }
        } catch (e) {
            if (count) count.textContent = '';
            grid.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-circle"></i>
                        Error al cargar productos. Intenta de nuevo.
                    </div>
                </div>`;
        }
    },

    // ========================================================================
    // RENDERIZADO DE PRODUCTOS
    // ========================================================================

    /**
     * Renderiza las tarjetas de producto en el grid.
     * Aplica filtro defensivo para ocultar productos sin stock al público.
     */
    renderProducts(products) {
        const grid = document.getElementById('products-grid');
        if (!grid) return;

        // --- Filtro defensivo ---
        const isAdmin = API.isAdmin();
        const visibleProducts = isAdmin
            ? products
            : products.filter(p => p.is_available && p.stock > 0);

        if (visibleProducts.length === 0) {
            grid.innerHTML = `
                <div class="col-12 text-center py-5 fade-in">
                    <i class="bi bi-inbox display-1 text-muted"></i>
                    <h4 class="mt-3">Sin resultados</h4>
                    <p class="text-muted">Prueba ajustando los filtros de búsqueda.</p>
                    <button class="btn btn-hs-outline" onclick="Catalog.clearFilters()">
                        <i class="bi bi-arrow-clockwise"></i> Limpiar filtros
                    </button>
                </div>`;
            return;
        }

        grid.innerHTML = visibleProducts.map((p, i) => {
            // --- Determinar badge y estado de stock ---
            let badgeHtml = '';
            let stockClass = '';
            let stockLabel = '';

            if (!p.is_available || p.stock === 0) {
                badgeHtml = '<span class="badge-hs badge-out">Agotado</span>';
                stockClass = 'text-danger';
                stockLabel = 'Sin stock';
            } else if (p.stock <= 3) {
                badgeHtml = `<span class="badge-hs badge-low">¡Últimas ${p.stock}!</span>`;
                stockClass = 'text-danger';
                stockLabel = `¡Solo ${p.stock} disponibles!`;
            } else if (p.stock <= 5) {
                badgeHtml = `<span class="badge-hs badge-low">Últimas ${p.stock}</span>`;
                stockClass = 'text-warning';
                stockLabel = `${p.stock} disponibles`;
            } else if (p.stock <= 10) {
                stockClass = 'text-success';
                stockLabel = `${p.stock} disponibles`;
            } else {
                stockClass = 'text-muted';
                stockLabel = `${p.stock} disponibles`;
            }

            return `
                <div class="col-6 col-md-4 col-xxl-3 fade-in" style="animation-delay: ${i * 0.05}s;">
                    <div class="product-card">
                        <div class="product-image-wrapper">
                            <div class="product-badges">${badgeHtml}</div>
                            ${p.image
                                ? `<img src="${p.image}" alt="${escapeHtml(p.name)}" loading="lazy">`
                                : `<i class="bi bi-cpu placeholder-icon"></i>`}
                        </div>
                        <div class="product-body">
                            <span class="product-brand">${escapeHtml(p.brand_name || '—')}</span>
                            <h3 class="product-title">${escapeHtml(p.name)}</h3>
                            <span class="product-category">
                                <i class="bi bi-tag"></i> ${escapeHtml(p.category_name || '—')}
                            </span>
                            <div class="product-price-row">
                                <div>
                                    <div class="product-price">${formatCLP(p.price)}</div>
                                    <small class="product-stock ${stockClass}">
                                        <i class="bi bi-box-seam"></i> ${stockLabel}
                                    </small>
                                </div>
                            </div>
                            <div class="d-grid gap-2 mt-3">
                                <button class="btn btn-hs-primary btn-sm"
                                        onclick="Catalog.addToCart(${p.id})"
                                        ${!p.is_available ? 'disabled' : ''}>
                                    <i class="bi bi-cart-plus"></i>
                                    ${p.is_available ? 'Agregar' : 'Agotado'}
                                </button>
                                <a href="/producto/${p.id}/" class="btn btn-hs-outline btn-sm">
                                    <i class="bi bi-eye"></i> Ver detalle
                                </a>
                            </div>
                        </div>
                    </div>
                </div>`;
        }).join('');
    },

    // ========================================================================
    // PAGINACIÓN
    // ========================================================================

    /**
     * Renderiza la paginación con botones anterior/siguiente.
     */
    renderPagination(data) {
        const container = document.getElementById('pagination');
        if (!container) return;

        if (!data.next && !data.previous) {
            container.innerHTML = '';
            return;
        }

        container.innerHTML = `
            <nav>
                <ul class="pagination justify-content-center">
                    <li class="page-item ${!data.previous ? 'disabled' : ''}">
                        <a class="page-link" href="#"
                           onclick="Catalog.goToPage(${this.filters.page - 1}); return false;">
                            <i class="bi bi-chevron-left"></i> Anterior
                        </a>
                    </li>
                    <li class="page-item active">
                        <span class="page-link">Página ${this.filters.page}</span>
                    </li>
                    <li class="page-item ${!data.next ? 'disabled' : ''}">
                        <a class="page-link" href="#"
                           onclick="Catalog.goToPage(${this.filters.page + 1}); return false;">
                            Siguiente <i class="bi bi-chevron-right"></i>
                        </a>
                    </li>
                </ul>
            </nav>
        `;
    },

    goToPage(page) {
        if (page < 1) return;
        this.filters.page = page;
        this.loadProducts();
        document.getElementById('products-grid')?.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
        });
    },

    // ========================================================================
    // FILTROS
    // ========================================================================

    /**
     * Aplica los filtros del formulario lateral y sincroniza los chips.
     */
    applyFilters(event) {
        if (event) event.preventDefault();

        this.filters.search = document.getElementById('filter-search').value.trim();
        this.filters.category = document.getElementById('filter-category').value;
        this.filters.brand = document.getElementById('filter-brand').value;
        this.filters.price_min = document.getElementById('filter-price-min').value;
        this.filters.price_max = document.getElementById('filter-price-max').value;
        this.filters.in_stock = document.getElementById('filter-in-stock').checked;
        this.filters.ordering = document.getElementById('filter-ordering').value;
        this.filters.page = 1;

        this.syncChips();
        this.loadProducts();
    },

    /**
     * Limpia los filtros, resetea el formulario y sincroniza los chips.
     */
    clearFilters() {
        document.getElementById('filter-form').reset();
        this.filters = {
            search: '',
            category: '',
            brand: '',
            price_min: '',
            price_max: '',
            in_stock: false,
            ordering: '-created_at',
            page: 1,
        };

        this.syncChips();
        this.loadProducts();
    },

    // ========================================================================
    // BUSCADOR DEL HERO
    // ========================================================================

    /**
     * Sincroniza el buscador del hero con el filtro lateral y busca.
     * Se invoca al hacer clic en el botón "Buscar" del hero o al presionar
     * Enter dentro del input del hero.
     */
    heroSearch() {
        const heroInput = document.getElementById('hero-search-input');
        const filterInput = document.getElementById('filter-search');

        if (!heroInput || !filterInput) return;

        const q = heroInput.value.trim();
        filterInput.value = q;

        this.applyFilters();

        document.getElementById('products-grid')?.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
        });
    },

    // ========================================================================
    // AGREGAR AL CARRO
    // ========================================================================

    /**
     * Agrega un producto al carro del usuario autenticado.
     */
    async addToCart(productId) {
        if (!API.isAuthenticated()) {
            showFlash('Debes iniciar sesión para agregar al carro.', 'warning');
            setTimeout(() => window.location.href = '/login/', 800);
            return;
        }

        try {
            await API.post('/api/cart/items/', { product_id: productId, quantity: 1 });
            showFlash('Producto agregado al carro.', 'success');
            Auth.updateCartBadge();
        } catch (e) {
            // DRF puede devolver string o lista según cómo se lance el error
            const pick = v => (Array.isArray(v) ? v[0] : v);
            const msg = pick(e.data?.quantity)
                || pick(e.data?.product)
                || e.data?.detail
                || 'Error al agregar el producto.';
            showFlash(msg, 'danger');
        }
    },

    // ========================================================================
    // DETALLE DE PRODUCTO
    // ========================================================================

    /**
     * Carga el detalle de un producto (para product_detail.html).
     */
    async loadProductDetail(productId) {
        const container = document.getElementById('product-detail');
        if (!container) return;

        try {
            const p = await API.get(`/api/products/${productId}/`);

            // --- Determinar estado de stock ---
            let stockBadge = '';
            let stockAlert = '';
            let buttonDisabled = !p.is_available;

            if (!p.is_active) {
                stockBadge = `<span class="badge text-bg-secondary">Descontinuado</span>`;
                stockAlert = `
                    <div class="alert alert-secondary">
                        <i class="bi bi-info-circle"></i>
                        Este producto ya no está disponible en el catálogo.
                    </div>`;
            } else if (p.stock === 0) {
                stockBadge = `<span class="badge text-bg-danger">Agotado</span>`;
                stockAlert = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle"></i>
                        <strong>Producto agotado.</strong>
                        Vuelve pronto para ver si hay nuevas unidades.
                    </div>`;
            } else if (p.stock <= 5) {
                stockBadge = `<span class="badge text-bg-warning">¡Últimas ${p.stock} unidades!</span>`;
                stockAlert = `
                    <div class="alert alert-warning">
                        <i class="bi bi-lightning-charge"></i>
                        <strong>Stock limitado:</strong> solo quedan ${p.stock} unidades disponibles.
                    </div>`;
            } else {
                stockBadge = `<span class="badge text-bg-success">${p.stock} disponibles</span>`;
            }

            container.innerHTML = `
                <div class="row g-4">
                    <div class="col-md-5">
                        ${p.image
                            ? `<img src="${p.image}" class="img-fluid rounded shadow-sm" alt="${escapeHtml(p.name)}">`
                            : `<div class="bg-body-tertiary rounded d-flex align-items-center justify-content-center" style="height:350px;">
                                 <i class="bi bi-cpu display-1 text-secondary"></i>
                               </div>`}
                    </div>
                    <div class="col-md-7">
                        <small class="text-muted text-uppercase">
                            ${escapeHtml(p.category.name)} · ${escapeHtml(p.brand.name)}
                        </small>
                        <h2 class="fw-bold mt-2">${escapeHtml(p.name)}</h2>
                        <p class="text-muted">SKU: <code>${escapeHtml(p.sku)}</code></p>
                        <div class="fs-2 fw-bold text-primary my-3">${formatCLP(p.price)}</div>
                        <p>${escapeHtml(p.description || 'Sin descripción.')}</p>
                        <p class="mb-3">${stockBadge}</p>
                        ${stockAlert}
                        <button class="btn btn-hs-primary btn-lg"
                                onclick="Catalog.addToCart(${p.id})"
                                ${buttonDisabled ? 'disabled' : ''}>
                            <i class="bi bi-cart-plus"></i>
                            ${buttonDisabled ? 'No disponible' : 'Agregar al carro'}
                        </button>
                    </div>
                </div>`;
        } catch (e) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-circle"></i>
                    Producto no encontrado.
                </div>`;
        }
    },
};