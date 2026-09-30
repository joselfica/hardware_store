/**
 * ============================================================================
 * ANIMACIONES SUTILES - Hardware Store
 * ============================================================================
 * Micro-interacciones que dan vida a la web sin caer en lo exagerado.
 *
 * Todas las animaciones:
 *   - Duran ≤ 400ms.
 *   - Usan solo `transform` y `opacity` (GPU-accelerated).
 *   - Respetan `prefers-reduced-motion`.
 *   - Se inicializan una sola vez y usan IntersectionObserver cuando aplica.
 *
 * Autor: José Fica
 * Sección: AP-N4-C2
 * Año: 2026
 * ============================================================================
 */

const Animations = {
    // ========================================================================
    // CONFIGURACIÓN
    // ========================================================================

    /**
     * Detecta si el usuario prefiere movimiento reducido (accesibilidad).
     * Si es True, se desactivan todas las animaciones.
     */
    prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    },

    // ========================================================================
    // 1. FADE-IN AL SCROLL (reveal on scroll)
    // ========================================================================
    // Aplica una animación de entrada a los elementos cuando entran al
    // viewport. Usa IntersectionObserver para performance.
    //
    // Uso: agrega `data-animate="fade-up"` a cualquier elemento HTML.
    // ========================================================================

    initScrollReveal() {
        if (this.prefersReducedMotion()) return;

        const elements = document.querySelectorAll('[data-animate]');
        if (elements.length === 0) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        const delay = entry.target.dataset.delay || 0;
                        setTimeout(() => {
                            entry.target.classList.add('animated');
                        }, parseInt(delay));
                        observer.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px',
            }
        );

        elements.forEach((el) => observer.observe(el));
    },

    // ========================================================================
    // 2. PARALLAX SUTIL EN EL HERO
    // ========================================================================
    // Mueve los elementos decorativos del hero ligeramente al hacer scroll.
    // Aplica un factor muy pequeño (0.15) para que sea sutil.
    // ========================================================================

    initHeroParallax() {
        if (this.prefersReducedMotion()) return;

        const hero = document.querySelector('.hero-compact, .hero');
        if (!hero) return;

        let ticking = false;

        const update = () => {
            const scrolled = window.pageYOffset;
            // Los pseudo-elementos ::before y ::after se mueven con CSS
            // Aquí movemos solo el contenido del hero
            const content = hero.querySelector('.hero-compact__inner, .hero-content');
            if (content) {
                content.style.transform = `translateY(${scrolled * 0.15}px)`;
            }
            ticking = false;
        };

        window.addEventListener('scroll', () => {
            if (!ticking) {
                window.requestAnimationFrame(update);
                ticking = true;
            }
        }, { passive: true });
    },

    // ========================================================================
    // 3. CONTADOR ANIMADO (hero stats)
    // ========================================================================
    // Anima los números del hero (ej: +500 productos) desde 0 hasta el valor
    // final. Usa una curva ease-out para que sea natural.
    //
    // Uso: <strong data-count="500">0</strong>
    // ========================================================================

    initCounters() {
        if (this.prefersReducedMotion()) return;

        const counters = document.querySelectorAll('[data-count]');
        if (counters.length === 0) return;

        const animate = (el) => {
            const target = parseInt(el.dataset.count);
            const duration = 1200; // 1.2s
            const start = performance.now();
            const prefix = el.dataset.prefix || '';
            const suffix = el.dataset.suffix || '';

            const step = (now) => {
                const elapsed = now - start;
                const progress = Math.min(elapsed / duration, 1);
                // Ease-out cubic
                const eased = 1 - Math.pow(1 - progress, 3);
                const value = Math.floor(eased * target);
                el.textContent = `${prefix}${value.toLocaleString('es-CL')}${suffix}`;
                if (progress < 1) {
                    requestAnimationFrame(step);
                } else {
                    el.textContent = `${prefix}${target.toLocaleString('es-CL')}${suffix}`;
                }
            };

            requestAnimationFrame(step);
        };

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        animate(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.5 }
        );

        counters.forEach((el) => observer.observe(el));
    },

    // ========================================================================
    // 4. RIPPLE EFFECT EN BOTONES
    // ========================================================================
    // Añade un efecto de onda al hacer clic en cualquier botón. Es un detalle
    // sutil que da feedback inmediato al usuario.
    // ========================================================================

    initButtonRipple() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn, .chip');
            if (!btn) return;
            if (this.prefersReducedMotion()) return;

            const rect = btn.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            const ripple = document.createElement('span');
            ripple.className = 'ripple-effect';
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;

            btn.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    },

    // ========================================================================
    // 5. NAVBAR SCROLL EFFECT
    // ========================================================================
    // Añade una sombra al navbar cuando el usuario hace scroll hacia abajo.
    // Da sensación de "profundidad" al navegar.
    // ========================================================================

    initNavbarScroll() {
        const navbar = document.querySelector('.navbar-hs');
        if (!navbar) return;

        let lastScroll = 0;

        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;

            if (currentScroll > 20) {
                navbar.classList.add('navbar-scrolled');
            } else {
                navbar.classList.remove('navbar-scrolled');
            }

            // Ocultar navbar al hacer scroll hacia abajo (más de 200px)
            if (currentScroll > lastScroll && currentScroll > 200) {
                navbar.classList.add('navbar-hidden');
            } else {
                navbar.classList.remove('navbar-hidden');
            }

            lastScroll = currentScroll;
        }, { passive: true });
    },

    // ========================================================================
    // 6. TYPING EFFECT (hero h1)
    // ========================================================================
    // Añade un efecto de "máquina de escribir" sutil al subtítulo del hero.
    // Solo se aplica si el elemento tiene el atributo data-typing.
    // ========================================================================

    initTypingEffect() {
        if (this.prefersReducedMotion()) return;

        const el = document.querySelector('[data-typing]');
        if (!el) return;

        const text = el.dataset.typing;
        el.textContent = '';
        el.style.borderRight = '2px solid currentColor';

        let i = 0;
        const type = () => {
            if (i < text.length) {
                el.textContent += text.charAt(i);
                i++;
                setTimeout(type, 50);
            } else {
                // Parpadeo del cursor (opcional, se detiene después)
                setTimeout(() => {
                    el.style.borderRight = 'none';
                }, 1000);
            }
        };

        // Empezar cuando el elemento sea visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    setTimeout(type, 300);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        observer.observe(el);
    },

    // ========================================================================
    // 7. HOVER SUAVE EN CARDS DE PRODUCTO
    // ========================================================================
    // Aplica un efecto de inclinación 3D muy sutil al pasar el mouse sobre
    // las cards de productos. Máximo 3-4 grados para que sea imperceptible.
    // ========================================================================

    initCardTilt() {
        if (this.prefersReducedMotion()) return;
        // Solo en dispositivos con mouse (no táctil)
        if (window.matchMedia('(hover: none)').matches) return;

        const cards = document.querySelectorAll('.product-card');

        cards.forEach((card) => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const rotateX = ((y - centerY) / centerY) * 2; // máx 2 grados
                const rotateY = ((centerX - x) / centerX) * 2;

                card.style.transform = `
                    perspective(1000px)
                    rotateX(${rotateX}deg)
                    rotateY(${rotateY}deg)
                    translateY(-6px)
                `;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
            });
        });
    },

    // ========================================================================
    // 8. SCROLL SUAVE A ANCLAS
    // ========================================================================
    // Intercepta clics en enlaces con href="#..." y hace scroll suave.
    // ========================================================================

    initSmoothScroll() {
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href^="#"]');
            if (!link) return;

            const targetId = link.getAttribute('href');
            if (targetId === '#' || targetId === '') return;

            const target = document.querySelector(targetId);
            if (!target) return;

            e.preventDefault();
            target.scrollIntoView({
                behavior: this.prefersReducedMotion() ? 'auto' : 'smooth',
                block: 'start',
            });
        });
    },

    // ========================================================================
    // 9. FADE-IN DE IMÁGENES AL CARGAR
    // ========================================================================
    // Aplica un fade-in suave cuando las imágenes terminan de cargar.
    // Evita el "pop-in" brusco.
    // ========================================================================

    initImageFadeIn() {
        const images = document.querySelectorAll('img[loading="lazy"]');
        images.forEach((img) => {
            if (img.complete) {
                img.classList.add('img-loaded');
            } else {
                img.addEventListener('load', () => {
                    img.classList.add('img-loaded');
                });
            }
        });
    },

    // ========================================================================
    // 10. BADGE DEL CARRO CON PULSO
    // ========================================================================
    // Cuando el carro cambia de cantidad, hace un pulso al badge para llamar
    // la atención del usuario.
    // ========================================================================

    pulseCartBadge() {
        const badge = document.getElementById('cart-badge');
        if (!badge) return;

        badge.classList.remove('cart-badge-pulse');
        // Forzar reflow para reiniciar la animación
        void badge.offsetWidth;
        badge.classList.add('cart-badge-pulse');

        setTimeout(() => {
            badge.classList.remove('cart-badge-pulse');
        }, 500);
    },

    // ========================================================================
    // INICIALIZACIÓN GLOBAL
    // ========================================================================

    init() {
        this.initScrollReveal();
        this.initHeroParallax();
        this.initCounters();
        this.initButtonRipple();
        this.initNavbarScroll();
        this.initTypingEffect();
        this.initCardTilt();
        this.initSmoothScroll();
        this.initImageFadeIn();
    },
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => Animations.init());