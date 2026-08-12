document.addEventListener("DOMContentLoaded", () => {
    // 1. Navbar Scroll Blur Effect
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 20) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // 2. Scroll Reveal Animations using IntersectionObserver
    const revealElements = document.querySelectorAll('.reveal-on-scroll');
    if (revealElements.length > 0) {
        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.15,
            rootMargin: "0px 0px -50px 0px"
        });

        revealElements.forEach(el => revealObserver.observe(el));
    }

    // 3. Signature Tilt Effect (from Website)
    const signature = document.getElementById("curioraSignature");
    if (signature) {
        const glass = signature.querySelector(".signature-glass");
        const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        if (glass && !prefersReducedMotion) {
            signature.addEventListener("pointermove", (event) => {
                const rect = signature.getBoundingClientRect();
                const x = event.clientX - rect.left;
                const y = event.clientY - rect.top;

                const percentX = (x / rect.width) * 100;
                const percentY = (y / rect.height) * 100;

                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const rotateY = ((x - centerX) / centerX) * 8;
                const rotateX = ((centerY - y) / centerY) * 6;

                glass.style.setProperty("--mouse-x", `${percentX}%`);
                glass.style.setProperty("--mouse-y", `${percentY}%`);

                glass.style.transform = `perspective(700px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(8px)`;
            });

            signature.addEventListener("pointerleave", () => {
                glass.style.setProperty("--mouse-x", "50%");
                glass.style.setProperty("--mouse-y", "50%");
                glass.style.transform = "perspective(700px) rotateX(0deg) rotateY(0deg) translateZ(0)";
            });
        }
    }
});
