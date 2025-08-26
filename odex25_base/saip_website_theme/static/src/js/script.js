// $(document).ready(function () {

//     if (window.location.pathname.match(/^\/web\/login/)) {
//         $("body").addClass("login_page")
//     };

// });

(function () {
    if (window.location.pathname.match(/^\/(en|ar)?\/web\/login$|^\/web\/login$/)) {
        $("body").addClass("login_page");
    }

    let global_env = ['<i class="mdi mdi-chevron-left"/>','<i class="mdi mdi-chevron-right"/>'];
    if($('#wrapwrap').hasClass('o_rtl')){
        $(".pagination li:first-child a").html(global_env[1]);
        $(".pagination li:last-child a").html(global_env[0]);
    }else{
        $(".pagination li:first-child a").html(global_env[0]);
        $(".pagination li:last-child a").html(global_env[1]);
        console.log("paginations")
    }

})();


