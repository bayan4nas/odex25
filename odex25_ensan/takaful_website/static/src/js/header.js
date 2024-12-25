$(document).ready(function() {
    // language switcher Conditions displays based on website active langauge
    if ($('#wrapwrap').hasClass('o_rtl')) {
        $('[data-url_code="en"]').show();
        $('[data-url_code="ar"]').hide();
    } else {
        $('[data-url_code="ar"]').show();
        $('[data-url_code="en"]').hide();
    }
    
    // Hide Text Inside add language link and keeping the icon only
    $('.o_add_language').contents().filter(function () {
        return this.nodeType === 3;
    }).replaceWith('');
});