// $(document).ready(function () {

//     if (window.location.pathname.match(/^\/web\/login/)) {
//         $("body").addClass("login_page")
//     };

// });

$(document).ready(function () {
    if (window.location.pathname.match(/^\/(en|ar)?\/web\/login$|^\/web\/login$/)) {
        $("body").addClass("login_page");
    }
});


