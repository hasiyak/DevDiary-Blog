/**
 * DevDiary Modern Animations & Micro-Interactions (animations.js)
 * Implements lightweight IntersectionObserver reveals, reading progress bar,
 * animated stats counters, and floating back-to-top button.
 */

document.addEventListener('DOMContentLoaded', function() {

    // --------------------------------------------------------------------------
    // 1. Reading Progress Bar
    // --------------------------------------------------------------------------
    const progressBar = document.getElementById('readingProgressBar');
    if (progressBar) {
        let isTicking = false;

        function updateProgressBar() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            if (docHeight > 0) {
                const scrollPercent = Math.min(100, Math.max(0, (scrollTop / docHeight) * 100));
                progressBar.style.width = scrollPercent + '%';
            }
            isTicking = false;
        }

        window.addEventListener('scroll', function() {
            if (!isTicking) {
                window.requestAnimationFrame(updateProgressBar);
                isTicking = true;
            }
        }, { passive: true });
    }

    // --------------------------------------------------------------------------
    // 2. Scroll-Triggered Reveal Animations (IntersectionObserver)
    // --------------------------------------------------------------------------
    const revealElements = document.querySelectorAll(
        '.reveal-on-scroll, .reveal-left, .reveal-right, .reveal-scale'
    );

    if ('IntersectionObserver' in window && revealElements.length > 0) {
        const revealObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-revealed');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            root: null,
            threshold: 0.1,
            rootMargin: '0px 0px -30px 0px'
        });

        revealElements.forEach(function(el) {
            revealObserver.observe(el);
        });
    } else {
        // Fallback for older browsers without IntersectionObserver
        revealElements.forEach(function(el) {
            el.classList.add('is-revealed');
        });
    }

    // --------------------------------------------------------------------------
    // 3. Animated Number Counters (Community Stats)
    // --------------------------------------------------------------------------
    const counterElements = document.querySelectorAll('[data-counter-target]');

    if (counterElements.length > 0) {
        function animateCounter(el) {
            const target = parseInt(el.getAttribute('data-counter-target'), 10);
            const suffix = el.getAttribute('data-counter-suffix') || '';
            const prefix = el.getAttribute('data-counter-prefix') || '';
            const duration = 1600; // ms
            const startTime = performance.now();

            function updateCounter(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                // Ease out cubic
                const easeProgress = 1 - Math.pow(1 - progress, 3);
                const currentVal = Math.floor(easeProgress * target);

                el.innerText = prefix + currentVal.toLocaleString() + suffix;

                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                } else {
                    el.innerText = prefix + target.toLocaleString() + suffix;
                }
            }

            requestAnimationFrame(updateCounter);
        }

        if ('IntersectionObserver' in window) {
            const counterObserver = new IntersectionObserver(function(entries, observer) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        animateCounter(entry.target);
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.25 });

            counterElements.forEach(function(el) {
                counterObserver.observe(el);
            });
        } else {
            counterElements.forEach(animateCounter);
        }
    }

    // --------------------------------------------------------------------------
    // 4. Floating "Back to Top" Button
    // --------------------------------------------------------------------------
    const backToTopBtn = document.getElementById('backToTopBtn');
    if (backToTopBtn) {
        let isScrollTicking = false;

        function toggleBackToTop() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            if (scrollTop > 350) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
            isScrollTicking = false;
        }

        window.addEventListener('scroll', function() {
            if (!isScrollTicking) {
                window.requestAnimationFrame(toggleBackToTop);
                isScrollTicking = true;
            }
        }, { passive: true });

        backToTopBtn.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
});

