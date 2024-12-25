$(document).ready(function() {
    $('.main-slider').owlCarousel({
        loop: true,
        margin: 0,
        nav: true,
        dots: true,
        rtl: true,
        animateOut: 'fadeOut',
        animateIn: 'fadeIn',
        navText: ['<i class="mdi mdi-chevron-right"></i>', '<i class="mdi mdi-chevron-left"></i>'],
        responsive: {
            0: {
                items: 1
            },
            600: {
                items: 1
            },
            1000: {
                items: 1
            }
        }
    });

    $('.news-slider').owlCarousel({
        loop: true,
        nav: false,
        items: 3,
        lazyLoad: true,
        rtl: true,
        nav: true,
        center: true,
        navText: ['<i class="mdi mdi-chevron-right"></i>', '<i class="mdi mdi-chevron-left"></i>'],
        responsive: {
            0: {
                items: 1,
                stagePadding: 60
            },
            600: {
                items: 1,
                stagePadding: 100
            },
            1000: {
                items: 1,
                stagePadding: 200
            },
            1200: {
                items: 1,
                stagePadding: 150
            },
            1400: {
                items: 1,
                stagePadding: 300
            },
            1600: {
                items: 3,
                stagePadding: 0
            },
            1800: {
                items: 1,
                stagePadding: 400
            }
        }
    });



    $('.parteners-logo-slider').owlCarousel({
        loop: true,
        nav: false,
        dots: true,
        autoplay: true,
        items: 1,
        margin: 50,
        lazyLoad: true,
        rtl: true,
        center: true,
        responsive: {
            0: {
                items: 1,
            },
            600: {
                items: 3,
            },
            1000: {
                items: 6,
            },
        }
    });
});
