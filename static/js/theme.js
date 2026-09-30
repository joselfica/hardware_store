/**
 * ============================================================================
 * TEMA CLARO/OSCURO
 * ============================================================================
 * Permite alternar entre tema claro y oscuro, persistiendo la preferencia
 * en localStorage. Se aplica antes del render para evitar "flash of unstyled
 * content" (FOUC).
 *
 * IMPORTANTE — Doble atributo:
 *   - data-theme:      usado por nuestro sistema de diseño (styles.css).
 *   - data-bs-theme:   usado por Bootstrap 5.3+ para tematizar modales,
 *                      dropdowns, tablas, formularios, botones nativos, etc.
 *   Ambos DEBEN sincronizarse siempre.
 * ============================================================================
 */

const Theme = {
    STORAGE_KEY: 'hs_theme',

    init() {
        // Aplicar tema guardado o preferencia del sistema
        const stored = localStorage.getItem(this.STORAGE_KEY);
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = stored || (prefersDark ? 'dark' : 'light');
        this.apply(theme);
    },

    toggle() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        this.apply(next);
        localStorage.setItem(this.STORAGE_KEY, next);
    },

    apply(theme) {
        const html = document.documentElement;

        // 1. Atributo propio (usado por styles.css)
        html.setAttribute('data-theme', theme);

        // 2. Atributo de Bootstrap 5.3 (modales, dropdowns, forms, etc.)
        html.setAttribute('data-bs-theme', theme);

        // 3. Actualizar el ícono del toggle si existe en el DOM
        const icon = document.getElementById('theme-icon');
        if (icon) {
            icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars';
        }
    },
};

// ============================================================================
// APLICACIÓN INMEDIATA (evita FOUC)
// ============================================================================
// Este bloque se ejecuta al parsear el <head> del documento, antes de que
// el <body> se renderice. Aplica el tema antes del primer paint.
// ============================================================================
(function() {
    const stored = localStorage.getItem('hs_theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = stored || (prefersDark ? 'dark' : 'light');

    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-bs-theme', theme);
})();