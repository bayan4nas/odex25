$(document).ready(function () {

    let sponsorships_group_api = "/portal/sponsor/sponsorships/create/";
    $('form#group_sponsorship').on('submit', function (evt) {
        evt.preventDefault();
        var formData = new FormData(this);
        var selectedValues = $('#benefit_ids').val() || []; 
        var selectedValuesJSON = JSON.stringify(selectedValues);
        formData.append('benefit_ids', selectedValuesJSON);
        console.log(formData);
        $.ajax({
            type: "POST",
            url: sponsorships_group_api,
            data: formData,
            processData: false,
            contentType: false,
            dataType: 'json',
            success: function (response) {
                console.log(response);
                if (response.status === true) {
                    $('.sponsorship_creation_feedback').show();
                    $('.sponsorship_creation_feedback').html(`<p class="alert alert-success text-center">  ${response.msg} </p>`);
                    setTimeout(function () {
                        $('.sponsorship_creation_feedback').hide();
                        location.reload();
                    }, 3000);
                } else {
                    $('.sponsorship_creation_feedback').show();
                    $('.sponsorship_creation_feedback').html(`<p class="alert alert-danger text-center">  ${response.msg} </p>`);
                    // setTimeout(function () {
                    //     $('.sponsorship_creation_feedback').hide();
                    //     // location.reload();
                    // }, 3000);
                }
            },
            error: function (err) {
                $('.sponsorship_creation_feedback').show();
                $('.sponsorship_creation_feedback').html(`<p class="alert alert-danger text-center">  ${err.msg}   </p>`)
            }
        });
    });



});

