$(document).ready(function () {
    const urlSearchParams = new URLSearchParams(window.location.search);
    const benefit_id = urlSearchParams.get("benefit_id");
    $("#benefit_id_contribution").val(benefit_id);

    let payment = "/portal/sponsor/paying_demo/save";
    $('form#contribution_form').on('submit', function (evt) {
        evt.preventDefault();
        var form_data = $(this).serialize();
        $.ajax({
            type: "POST",
            url: payment,
            data: form_data,
            dataType:'json',
            processData: false,
            success: function (response) {
                console.log(response);
                if (response.status === true) {
                    $('.gitf_feedback').show();
                    $('.gitf_feedback').html(`<p class="alert alert-success text-center">  ${response.msg} </p>`);
                    setTimeout(function () {
                        $('.gitf_feedback').hide();
                        location.reload();
                    }, 3000);
                } else {
                    $('.gitf_feedback').show();
                    $('.gitf_feedback').html(`<p class="alert alert-danger text-center">  ${response.msg} </p>`);
                    setTimeout(function () {
                        $('.gitf_feedback').hide();
                        // location.reload();
                    }, 3000);
                }
            },
            error: function (err) {
                $('.new_app').append(`<p class="alert alert-dander text-center">  يوجد مشكلة !!   </p>`)
            }
        });
    });
})