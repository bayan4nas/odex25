$(document).ready(function () {
    $('.trigger_sponsors_modal').click(function () {
        $('#sponsors_modal').modal('show');
    })
    // integrate the sponsors types API
    let typeURL = "/sponser/form";
    fetch(typeURL)
        .then(response => response.json())
        .then(res => {
            typeList = res.data;
            console.log(typeList);
            typeList.forEach(function (index) {
                $('#sponsprs_types').append(`<option id="${index.id}" value="${index.id}">${index.name} </option>`);
            })
        });


    let create_sponsor = "/sponsor/submit";
    $('form#sponsors_form_reg').on('submit', function (evt) {
        console.log('form is submitting now !!');
        evt.preventDefault();
        var sponsors_data = {
            id: $('#sponsors_form_reg #eid').val(),
            sponsor_type_id: $('#sponsprs_types').val(),
            partner_id: $('#userId').val(),
            event_id: $('#eventId').val(),
            url: $('#url').val()
        }
        $.ajax({
            url: `${create_sponsor}?id=${sponsors_data.id}&sponsor_type_id=${sponsors_data.sponsor_type_id}&partner_id=${sponsors_data.partner_id}&event_id=${sponsors_data.event_id}&url="${sponsors_data.url}"`,
            type: "POST",
            data: sponsors_data,
            success: function (response) {
                console.log(response);
                console.log('data sent successfully !!!');
                $('.new_sponsor').append(`<p class="alert alert-success"> ${response.msg} </p>`)
                setTimeout(function () {
                    $('.new_sponsor').hide();
                    location.reload();
                }, 4000);
            },
            error: function (err) {
                console.log(err);
            }
        });
    });
});

