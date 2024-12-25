$(document).ready(function() {
    // Commenting out the function call to avoid the 404 error
    // load lists data
    // Home.loadPartners('.parteners-logo-slider');

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

});

let Home = new Object({
    partnersURL: '/partnership_logos',
    partnersList: [],
    loadPartners: function(selector) {
        let parent = this;
        // $.ajax({
        //     url: parent.partnersURL,
        //     type: "GET",
        //     dataType: "json",
        //     beforeSend: function() {
        //         // $('.search-loading-layer').addClass('active');
        //     },
        //     success: function(response) {
        //         if (response !== undefined && response !== null) {
        //             if (response.status) {
        //                 parent.partnersList = response.content;
        //                 $.each(response.content, function(index) {
        //                     $(selector).append(`<div class="item"><img src="${response.content[index].logo}" /> </div>`);
        //                 });
        //                 $('.parteners-logo-slider').owlCarousel({
        //                     loop: true,
        //                     nav: false,
        //                     dots: true,
        //                     autoplay: true,
        //                     items: 1,
        //                     margin: 50,
        //                     lazyLoad: true,
        //                     rtl: true,
        //                     center: true,
        //                     responsive: {
        //                         0: {
        //                             items: 1,
        //                         },
        //                         600: {
        //                             items: 3,
        //                         },
        //                         1000: {
        //                             items: 6,
        //                         },
        //                     }
        //                 });
        //             }
        //         }
        //     },
        //     error: function(error) {
        //         console.log(error);
        //     }
        // });
    },
});