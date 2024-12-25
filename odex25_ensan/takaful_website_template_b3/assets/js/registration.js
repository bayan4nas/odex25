$(document).ready(function () {
    // load lists data
    Registration.loadCities('#city_id');
    $('#next-step-button').on('click',function () {
        console.log(this);
        let $active = $('.step.active');
        $active.addClass('completed');
        $('.step').removeClass('active');
        $('.step[data-taget="#section-account"]').addClass('active');
        $('.steper-step-content').removeClass('active');
        $('.steper-step-content#section-account').addClass('active');
    });

    $('form#registartionForm').on('submit',function () {
        let data = $(this).serialize();
        console.log("Form Data:",data);
        Registration.submitRegistration(data);
        return false;
    });
});

let Registration = new Object({
    url: 'http://46.101.130.111:8075/portal/create_account',
    citiesURL: '',
    citiesList: [],
    submitRegistration: function (data) {
        let parent = this;  
        $.ajax({
            url: parent.url,
            type: "POST",
            dataType: "json",
            data: data,
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
    loadCities: function (selector) {
        let parent = this;  
        $.ajax({
            url: parent.citiesURL,
            type: "GET",
            dataType: "json",
            beforeSend: function () {
                // $('.search-loading-layer').addClass('active');
            },
            success: function (response) {
                if(response !== undefined && response !== null){
                    parent.citiesList = response.cities;
                    $.foreach(response.cities,function (index) {
                        $(selector).append(`<option value="${response.cities[index][0]}">${response.cities[index][1]}</option>`);
                    })
                }
            },
            error: function (error) {
                console.log(error);
            }
        });
    },
    goToAccountActivation: function () {
        let $active = $('.step.active');
        $active.addClass('completed');
        $('.step').removeClass('active');
        $('.step[data-taget="#section-confirm"]').addClass('active');
        $('.steper-step-content').removeClass('active');
        $('.steper-step-content#section-confirm').addClass('active');
    }
});