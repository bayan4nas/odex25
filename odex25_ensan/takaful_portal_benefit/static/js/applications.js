$(document).ready(function () {

    // get the product units
    let units_api = "/benefit/types/uom"; 
    fetch(units_api)
        .then(res => res.json())
        .then(response => {
            if (response && response.result && response.result.length > 0) {
                let units = response.result[0].product_uom;
                units.forEach((data, i) => {
                    $('#uom_id').append(`<option value=${data.id}> ${data.name} </option>`)
                });
            } else {
                console.error('Invalid or empty response:', response);
            }
        })
        .catch(error => {
            console.error('Error fetching units:', error);
        });


    // // get the product units 
    // let units_api = "/benefit/types/uom";
    // fetch(units_api).then(res => res.json()).then(response => {
    //     let units = response.result[0].product_uom;
    //     units.forEach((data, i) => {
    //         $('#uom_id').append(`<option value=${data.id}> ${data.name} </option>`)
    //     });
    // })

    let applicationsAPI = "/services/appliancesFurniture/receive";
    // send applications handler
    const sendAppsHandler = () => {
        $('form#apps_fur_form').on('submit', function (evt) {
            evt.preventDefault();
            var form = $(this);
            var formData = new FormData();
            var formParams = form.serializeArray();
            $.each(form.find('input[type="file"]'), function (i, tag) {
                $.each($(tag)[0].files, function (i, file) {
                    formData.append(tag.name, file);
                });
            });
            $.each(formParams, function (i, val) {
                formData.append(val.name, val.value);
            });
            $.ajax({
                type: "POST",
                url: applicationsAPI,
                data: formData,
                processData: false,
                contentType: false,
                dataType: 'json',
                success: function (response) {
                    if (response.status) {
                        $('.new_app').show();
                        $('.new_app').text(response.msg).addClass('alert alert-success');
                        setTimeout(function () {
                            $('.new_app').hide();
                            // location.reload();
                        }, 3000);
                    } else {
                        $('.new_app').show();
                        $('.new_app').text(response.msg).addClass('alert alert-danger');
                        setTimeout(function () {
                            $('.new_app').hide();
                            // location.reload();
                        }, 5000);
                    }
                },
                error: function (err) {
                    $('.new_app').show();
                    $('.new_app').text(err.msg).addClass('alert alert-danger');
                    setTimeout(function () {
                        $('.new_app').hide();
                        // location.reload();
                    }, 5000);
                }
            });
        });
    }
    sendAppsHandler();

    // set lon and lat 

    var lat = $("#lat");
    var lon = $("#lon");
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(showPosition);
        } else {
            x.innerHTML = "Geolocation is not supported by this browser.";
        }
    }

    function showPosition(position) {
        lat.val(position.coords.latitude);
        lon.val(position.coords.longitude);
    }

    $('.setLocation').click(function () {
        getLocation();
    })
})