$(document).ready(function () {

    // get all needs categories 
    $.ajax({
        url: '/benefit/types/cat_need',
        type: 'GET',
        dataType: 'json',
        processData: false,
        success: function (response) {
            needs = response.result[0].needs_categories;
            console.log(needs);
            if (needs.length > 0) {
                needs.forEach((element, i) => {
                    $("#need_category").append(`<option value="${element.id}">${element.name}</option>`);
                });
            }
            else {
                $('#need_category').append(`<option selected="selected"> لايوجد احتياجات   لعرضها  </option> `)
            }
        },
        error: function (error) {
            $("#need_category").text(error.msg).addClass('alert alert-danger')
        }
    });


    // get needs type depend on need category id 

    // Listen for changes in the first select box
    $('#need_category').change(function () {
        var selectedOption = $(this).val(); // Get the selected option value
        // Clear the second select box
        $('#need_type_ids').empty();
        var api = `/benefit/get_need_by_cat/${selectedOption}`
        console.log(api);
        // Fetch data from the server based on the selected option
        $.ajax({
            url: api,
            method: 'GET',
            dataType:'json',
            success: function (response) {
                types = response.data;
                if (types.length > 0) {
                    types.forEach((element, i) => {
                        $("#need_type_ids").append(`<option value="${element.id}">${element.name}</option>`);
                    });
                }
                else {
                    $('#need_type_ids').append(`<option selected="selected"> لايوجد نتائج   لعرضها  </option> `)
                }
            },
            error: function (error) {
                $("#need_type_ids").append(`<option selected="selected"> ${error.msg} </option> `)
            }
        });
    });

    $('.new_donor').hide(); //hie the feedback div
    $('form#urgent_needs_form').on('submit', function (evt) {
        evt.preventDefault();
        var form_data = new FormData(this);
        $.ajax({
            url: '/benefit/request_need',
            method: 'POST',
            data: form_data,
            dataType: 'json',
            processData: false,
            contentType: false,
            success: function (response) {
                if (response.status) {
                    $('.new_donor').show();
                    $(".new_donor").text(response.msg).addClass('alert alert-success')
                    setTimeout(function () {
                        $('.new_donor').hide();
                        // location.reload();
                        // $('.zakat_modal').modal('hide');
                    }, 3000);
                } else {
                    $('.new_donor').show();
                    $(".new_donor").text(response.msg).addClass('alert alert-danger')
                    setTimeout(function () {
                        $('.new_donor').hide();
                        // location.reload();
                    }, 3000);
                }
            },
            error: function (err) {
                $('.new_donor').show();
                $(".new_donor").text(err.msg).addClass('alert alert-danger')
                setTimeout(function () {
                    $('.new_donor').hide();
                    // location.reload();
                }, 3000);
            }
        });
    });
})