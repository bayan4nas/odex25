$(document).ready(function() {
    // Remove the call to loadCities
    // Registration.loadCities('#city_id');
    Registration.defaultValue();
    $('#next-step-button').on('click', function() {
        console.log(this);
        let $active = $('.step.active');
        $active.addClass('completed');
        $('.step').removeClass('active');
        $('.step[data-taget="#section-account"]').addClass('active');
        $('.steper-step-content').removeClass('active');
        $('.steper-step-content#section-account').addClass('active');
        let account_type = $('input[name="specify"]:checked').val();
        $("input[name='account_type']").val(account_type);
        if (account_type === "benefit") {
            $('.marital_status').show();
            $('input#marital_status').removeProp('disabled');
        }
    });

    $('form#registartionForm').on('submit', function() {
        let data = $(this).serialize();
        Registration.submitRegistration(data);
        return false;
    });
});

let Registration = new Object({
    registrationURL: '/portal/create_account',
    verificationCodeURL: '/portal/',
    // citiesURL: '/volunteer/city',
    citiesList: [],
    currentUserID: 0,
    submitRegistration: function(data) {
        let parent = this;
        $.ajax({
            url: parent.registrationURL,
            type: "POST",
            dataType: "json",
            data: data,
            beforeSend: function() {
                $('.step-loader').addClass('show');
                $('.message-block').html('');
            },
            success: function(response) {
                if (response !== undefined && response !== null) {
                    if (response.status) {
                        parent.popular = response.content;
                        parent.goToAccountActivation();
                    } else {
                        $('.message-block').html(`<div class="alert alert-danger">${response.msg}</div>`);
                    }
                }
                setTimeout(function() {
                    $('.step-loader').removeClass('show');
                }, 3000);
            },
            error: function(error) {
                $('.message-block').html(`<div class="alert alert-danger">${error.responseJSON.msg}</div>`);
                setTimeout(function() {
                    $('.step-loader').removeClass('show');
                }, 3000);
            }
        });
    },
    submitVerificationCode: function() {
        let parent = this;
        $.ajax({
            url: parent.verificationCodeURL,
            type: "POST",
            dataType: "json",
            data: data,
            beforeSend: function() {
                $('.step-loader').addClass('show');
                $('.message-block').html('');
            },
            success: function(response) {
                if (response !== undefined && response !== null) {
                    // if (response.status) {
                    //     parent.popular = response.content;
                    //     parent.goToAccountActivation();
                    // } else {
                    //     $('.message-block').html(`<div class="alert alert-danger">${response.error_descrip}</div>`);
                    // }
                    console.log(response);
                }
                setTimeout(function() {
                    $('.step-loader').removeClass('show');
                }, 3000);
            },
            error: function(error) {
                $('.message-block').html(`<div class="alert alert-danger">${error.responseJSON.error_descrip}</div>`);
                setTimeout(function() {
                    $('.step-loader').removeClass('show');
                }, 3000);
            }
        });
    },
    // loadCities: function(selector) {
    //     let parent = this;
    //     $.ajax({
    //         url: parent.citiesURL,
    //         type: "GET",
    //         dataType: "json",
    //         beforeSend: function() {
    //             // $('.search-loading-layer').addClass('active');
    //         },
    //         success: function(response) {
    //             if (response !== undefined && response !== null) {
    //                 if (response.status) {
    //                     parent.citiesList = response.data;
    //                     $.each(response.data, function(index) {
    //                         $(selector).append(`<option value="${response.data[index]['id']}">${response.data[index]['name']}</option>`);
    //                     });
    //                 }
    //             }
    //         },
    //         error: function(error) {
    //             console.log(error);
    //         }
    //     });
    // },
    goToAccountActivation: function() {
        let $active = $('.step.active');
        $active.addClass('completed');
        $('.step').removeClass('active');
        $('.step[data-taget="#section-confirm"]').addClass('active');
        $('.steper-step-content').removeClass('active');
        $('.steper-step-content#section-confirm').addClass('active');
        let mode = $('#activation_mode').val();
        console.log(mode);
        if (mode === "sms") {
            $(".code-mode").show();
        } else if (mode === "email") {
            $(".mail-mode").show();
        }
    },
    defaultValue: function() {
        $('#first_name').val('ALT');
        $('#second_name').val('HAS');
        $('#middle_name').val('IBN');
        $('#family_name').val('AHM');
        $('#id_number').val('1231231');
        $('#mobile').val('12387123');
        $('#email').val('altahir@exp-sa.com');
    }
});