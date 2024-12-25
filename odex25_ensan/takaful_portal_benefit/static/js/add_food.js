$(document).ready(function () {
    // add resturant 
    $('form#add_rest_food').on('submit', function (evt) {
        evt.preventDefault();
        var form_data = $(this).serialize();
        // var id = $("#id_holder_input").val();
        var add_food_api = `/services/restaurant/add_food?id=1`;
        console.log(add_food_api);
        $.ajax({
            url: add_food_api,
            type: "POST",
            data: form_data,
            dataType: 'json',
            success: function (response) {
                if (response.status) {
                    $('.new_food').show();
                    $(".new_food").text(response.msg).addClass('alert alert-success')
                    setTimeout(function () {
                        $('.new_food').hide();
                        location.reload();
                    }, 3000);
                } else {
                    $('.new_food').show();
                    $(".new_food").text(response.msg).addClass('alert alert-danger')
                    setTimeout(function () {
                        $('.new_food').hide();
                        // location.reload();
                    }, 3000);
                }
            },
            error: function (err) {
                $('.new_food').show();
                $(".new_food").text(err.msg).addClass('alert alert-danger')
                setTimeout(function () {
                    $('.new_food').hide();
                    // location.reload();
                }, 3000);
            }
        });
    });
})