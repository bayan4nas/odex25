$(document).ready(function () {
    
    $('button[data-toggle="browse-file"]').on('click',function () {
        let selector = $(this).data('target');
        $(selector).click();
    });

    $('form#submit-account').on('submit',function () {
        Registration.submitRegistration();
        return false;
    });
});

let Registration = new Object({
    url: '',
    submitRegistration: function () {  
        $.ajax({
            url: '/portal/create_account',
            type: "POST",
            dataType: "json",
            beforeSend: function () {
                // $('.search-loading-layer').addClass('active');
            },
            success: function (response) {
                if(response !== undefined && response !== null){
                    parent.popular = response.content;
                }
            },
            error: function (error) {
                console.log(error);
            }
        });
    },
    submitVerificationCode: function () {
        
    },
    goToComplelte: function () {
        let $active = $('.step.active');
        $active.addClass('completed');
        $('.step').removeClass('active');
        $('.step[data-taget="#section-done"]').addClass('active');
        $('.steper-step-content').removeClass('active');
        $('.steper-step-content#section-done').addClass('active');
    }
});