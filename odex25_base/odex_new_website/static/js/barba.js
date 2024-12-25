odoo.define('odex_new_website.custom_scripts', function (require) {
    "use strict";

    $(document).ready(function () {
        // Temporary testing: Clear the 'firstVisit' flag for testing
        localStorage.removeItem('firstVisit');

        // Hide the main content, header, and footer initially
        const mainContent = $('#main-content');
        const websiteHeader = $('#top');
        const websiteFooter = $('footer');

        // Check if we are on the home page
        const isHomePage = window.location.pathname === '/';

        // Only hide on home page
        if (isHomePage) {
            mainContent.hide();
            websiteHeader.hide();
            websiteFooter.hide();
        } else {
            websiteHeader.show();
            websiteFooter.show();
            mainContent.show();
        }

        // First Visit Entrance Layer
        const firstVisit = localStorage.getItem('firstVisit');
        const entranceLayer = $('#entrance-layer');

        if (!firstVisit) {
            // Show the entrance layer by setting display to 'flex'
            entranceLayer.css('display', 'flex');
            localStorage.setItem('firstVisit', 'true');

            // GSAP Timeline for entrance animation
            const loader = gsap.timeline();
            loader.to('.inner-progress', { duration: 3.5, height: '100%' })
                .set(".slogan #logo-container .image #path-e, .slogan #logo-container .image #path-other", { opacity: 0, scale: 0.7, filter: "blur(10px)" }, .7)
                .to(".slogan #logo-container .image #path-e, .slogan #logo-container .image #path-other", { duration: 1, opacity: 1, scale: 1, filter: "blur(0px)", ease: "power1.out" }, .9)
                .fromTo(".our-slogan-title span",{ opacity: 0, y: 50, filter: "blur(10px)" }, { duration: 1, opacity: 1, y: 0, filter: "blur(0px)", stagger: 0.1 }, 1)
                .to('#logo-container', { duration: 1, opacity: 0, filter: "blur(10px)", x: 20 })
                .to('.our-slogan-title', { duration: 1, opacity: 0, filter: "blur(10px)", x: 20 }, '-=1')
                .to('.progress', { duration: 1, opacity: 0, filter: "blur(10px)", x: 20 }, '-=1')
                .eventCallback("onComplete", () => {
                    // After the entrance animation completes, slide up the entrance layer
                    setTimeout(() => {
                        // Start fading in the main content, header, and footer during entrance animation
                        mainContent.fadeIn(500);
                        websiteHeader.fadeIn(500);
                        websiteFooter.fadeIn(500);

                        // Slide up the entrance layer
                        entranceLayer.slideUp(600);
                        // New timeline starts after slideUp completes
                        const afterLoader = gsap.timeline();
                        afterLoader.from('.header', { duration: 1, filter: "blur(10px)", scale: 1.2 })
                        .from('.fading', { duration: 1, opacity: 0, filter: "blur(10px)" }, '-=.5')
                    });
                });

        } else {
            // If it's not the first visit, show the main content, header, and footer immediately
            if (isHomePage) {
                mainContent.show();
                websiteHeader.show();
                websiteFooter.show();
            }
        }
    });

    // Function to manage visibility of header and footer on other pages
    function showHeaderFooter() {
        const websiteHeader = $('#top');
        const websiteFooter = $('footer');

        // Show header and footer
        websiteHeader.fadeIn(500);
        websiteFooter.fadeIn(500);

        // Debugging
        console.log('Header and footer displayed:', websiteHeader.css('display'), websiteFooter.css('display'));
    }

    // Initialize Barba.js for Page Transitions
    if (typeof barba !== 'undefined') {
        barba.init({
            transitions: [{
                leave(data) {
                    // Code for transition out animation can be added here if needed
                    console.log('Leaving page:', data.current.url);
                },
                enter(data) {
                    const entranceLayer = $('#entrance-layer');

                    // Always reset header and footer visibility at the beginning of the enter transition
                    $('#top').css('display', 'block');
                    $('footer').css('display', 'block');

                    // Show header and footer at the start of the transition
                    showHeaderFooter();

                    console.log('Entering page:', data.next.url);

                    // Check if entering the home page
                    if (data.next.url === '/') {
                        entranceLayer.css('display', 'flex');

                        // Show the entrance layer for a short duration
                        setTimeout(() => {
                            // Start fading in main content, header, and footer during entrance animation
                            $('#main-content').fadeIn(500);
                            $('#top').fadeIn(500);
                            $('footer').fadeIn(500);

                            // Slide up the entrance layer
                            entranceLayer.slideUp(1000);
                        }, 4000);
                    } else {
                        // For other pages, ensure main content is shown immediately
                        $('#main-content').fadeIn(500);
                    }
                }
            }]
        });
    } else {
        console.error('Barba.js is not defined.');
    }
});
