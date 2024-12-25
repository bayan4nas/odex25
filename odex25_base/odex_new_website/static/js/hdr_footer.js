$(document).ready(function () {

    /////////////////////////////////////////////////////////////////////////////////////////////////////////////

    gsap.registerPlugin(ScrollTrigger);

    /////////////////////////////////////////////////////////////////////////////////////////////////////////////

    // Navbar // Hide Navbar Up
    const showAnim = gsap.from("nav.navbar", { yPercent: -100, paused: true, duration: 0.2 }).progress(1);

    // Navbar // Global ScrollTrigger to show the navbar anytime we scroll up
    let lastScrollY = window.scrollY;

    window.addEventListener("scroll", function () {
        let currentScrollY = window.scrollY;

        if (currentScrollY < lastScrollY) {
            // Scroll up detected
            showAnim.play();
        } else if (currentScrollY > lastScrollY) {
            // Scroll down detected
            showAnim.reverse();  
        }
        lastScrollY = currentScrollY;
    });

    /////////////////////////////////////////////////////////////////////////////////////////////////////////////

    // Navbar // Animate Navbar Background Based on Page & Element Existence
    const navbar = document.querySelector("nav.navbar");

    // Initial state
    gsap.set(navbar, {
        background: "transparent"
    });

    // Function to check and update navbar background
    function updateNavbarBackground() {
        const scrollY = window.scrollY;
        const coursesContainer = document.querySelector('.courses_show_case_container');

        if (coursesContainer && scrollY > coursesContainer.offsetTop - 100) {
            if ($('#entrance-layer').is(':hidden')) {
                gsap.to(navbar, {
                    background: "linear-gradient(210.92deg, #0CB28B 10.45%, #0C3A5A 93.09%)",
                    duration: 0.5
                });
            }
        } else {
            gsap.to(navbar, {
                background: "transparent",
                duration: 0.5
            });
        }
    }

    if (document.querySelector('.courses_show_case_container')) {
        ScrollTrigger.create({
            trigger: ".courses_show_case_container",
            start: "top-=100px top",
            end: "+=100px",
            scrub: true,
            onEnter: () => {
                if ($('#entrance-layer').is(':hidden')) {
                    gsap.to(navbar, {
                        background: "linear-gradient(210.92deg, #0CB28B 10.45%, #0C3A5A 93.09%)",
                        duration: 0.5
                    });
                }
            },
            onEnterBack: () => {
                if ($('#entrance-layer').is(':hidden')) {
                    gsap.to(navbar, {
                        background: "transparent",
                        duration: 0.5
                    });
                }
            },
            onLeaveBack: () => {
                gsap.to(navbar, {
                    background: "transparent",
                    duration: 0.5
                });
            },
        });

        $(window).on('scroll', updateNavbarBackground);
    } else {
        gsap.set(navbar, {
            background: "linear-gradient(210.92deg, #0CB28B 10.45%, #0C3A5A 93.09%)",
            duration: 0
        });
    }

    /////////////////////////////////////////////////////////////////////////////////////////////////////////////

    // Mobile Menu // Menu Icon & Mobile Popup Menu

    let menuBtn = document.getElementById("menu-btn-container");
    let mobileMenuOverlay = document.querySelector(".popup-overlay");
    let mobileMenuOverlayTransition = document.querySelector(".popup-overlay-transition");

    const mobileMenuAnimation = gsap.timeline({ paused: true })
    mobileMenuAnimation.to('.popup-container', { duration: .1, display: "block" })
        .to('.popup-overlay', { duration: .2, x: 0, ease: "expo.inOut" }, 0)
        .to('.popup-menu', { duration: .5, x: 0, ease: "expo.inOut" }, .3)
        .to(mobileMenuOverlayTransition, { duration: 1, width: "0px", ease: "expo.inOut" }, .3)


    // Open / Close Popup Menu

    if (menuBtn) {
        menuBtn.addEventListener("click", (e) => {
            e.preventDefault();
            menuBtn.classList.toggle("openmenu");

            if (menuBtn.classList.contains("openmenu")) {
                mobileMenuAnimation.play();
            } else {
                mobileMenuAnimation.reverse();
            }
        });
    }


    // Close From Overlay
    if (mobileMenuOverlay) {
        mobileMenuOverlay.addEventListener("click", (e) => {
            e.preventDefault();
            // mobileMenuAnimation.reverse()
            menuBtn.classList.toggle("openmenu");
            if (menuBtn.classList.contains("openmenu")) {
                mobileMenuAnimation.play();
            } else {
                mobileMenuAnimation.reverse();
            }
        });
    }

    /////////////////////////////////////////////////////////////////////////////////////////////////////////////

    // Footer // set the contact call number
    var footerCallLink = document.getElementById('call-link');
    if (footerCallLink) {
        footerCallLink.setAttribute('href', 'tel:009660545941651');
    } else {
        console.error("Element with ID 'call-link' not found.");
    }

    /////////////////////////////////////////////////////////////////////////////////////////////////////////////

    // Scroll To Top

    let scrollToTop = document.querySelector(".scroll-top");

    gsap.from(scrollToTop, {
        duration: 1,
        opacity: 0,
        scrollTrigger: {
            trigger: document.body,
            start: "100vh top",
            end: "bottom top",
            scrub: true
        }
    });

    if (scrollToTop) {
        scrollToTop.addEventListener("click", () => {
            gsap.to(window, { duration: 1, scrollTo: 0 });
        });
    }


})
