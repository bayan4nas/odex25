$(document).ready(function () {
    console.log('this is kafel js');
    //Get list of cities 
    let allCities = "/portal/sys/city_list";
    fetch(allCities).then(res => res.json()).then(cities => {
        console.log(cities);
        data = cities.results;
        data.forEach((city, i) => {
            $('#city_id').append(`<option value=${city.id}> ${city.name} </option>`)
        });
    });

})


var currentPage = 1;
var benefitType = 'orphan'; // Default value
var next
var prev


function loadData(page) {
    $.ajax({
        url: '/portal/sponsor/sponsorships/page/' + page,
        type: 'GET',
        data: { benefit_type: benefitType },
        dataType: 'json',
        success: function (data) {
            results = data.results;
            console.log(results);
            var html = '';
            if (data.status) {
                results.forEach((element, i) => {
                    html +=
                        `
                            <tr data-type="orphan" data-id="${element.benefit_id.id}" ${element.month_count >= 1 ? " class = 'active' " : " class= 'expired' "}>
                                <td> ${i + 1} </td>
                                <td> ${element.benefit_id.name} </td>
                                <td> ${element.benefit_id.gender} </td>
                                <td> ${element.benefit_id.age} </td>
                                <td> ${element.benefit_id.city_id} </td>
                                <td> ${element.benefit_id.benefit_type} </td>
                                <td> ${element.benefit_id.benefit_needs_percent} % </td>
                                <td> ${element.benefit_id.benefit_arrears_value} </td>
                                <td> ${element.start_date} </td>
                                <td> ${element.month_count >= 1 ? `<span class="active_td"> سارية </span>` : `<span class="expired_td"> منتهية </span>`} </td>
                            </tr>
                        `
                });
                $('.kafalaty_table tbody').html(html);
                next = data.next_page;
                prev = (currentPage > 1) ? currentPage - 1 : null;
                currentPage = page;
                console.log(next, prev);
            }
            else {
                console.log(data.msg);
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.log(textStatus + ': ' + errorThrown);
        }
    });
}

//cancelation resons list api 

$(document).ready(function () {
    let reasons = "/portal/sys/reason_list";
    fetch(reasons).then(res => res.json()).then(reasons => {
        data = reasons.results;
        console.log(data);
        data.forEach((reason, i) => {
            $('#reason_id').append(`<option value=${reason.id}> ${reason.name} </option>`)
        });
    });
})

//load benefits data 

function sponsorshipsCancelation(page) {
    $.ajax({
        url: '/portal/sponsor/sponsorships/page/' + page,
        type: 'GET',
        data: { benefit_type: benefitType },
        dataType: 'json',
        success: function (data) {
            results = data.results;
            console.log(results);
            var html = '';
            if (data.status) {
                results.forEach((element, i) => {
                    html +=
                        `
                            <tr ${element.month_count >= 1 ? " class = 'active' " : " class= 'expired' "}>
                                <td> ${i + 1} </td>
                                <td> ${element.benefit_id.name} </td>
                                <td> ${element.benefit_id.gender} </td>
                                <td> ${element.benefit_id.age} </td>
                                <td> ${element.benefit_id.city_id} </td>
                                <td> ${element.benefit_id.benefit_type} </td>
                                <td> ${element.benefit_id.benefit_needs_percent} % </td>
                                <td> ${element.benefit_id.benefit_arrears_value} </td>
                                <td> ${element.start_date} </td>
                                <td> ${element.month_count >= 1 ?
                            `
                                        <span class="active_td"> سارية </span>
                                        <a data-id= "${element.id}" href="#" class="cancel_link"> 
                                            <img src="/takaful_portal_sponsor/static/img/trash.png" alt="cancel" /> الغاء
                                        </a>
                                    `
                            :

                            `
                                        <span class="expired_td"> منتهية </span>
                                        <a data-id= "${element.id}" href="#" class="cancel_link"> 
                                            <img src="/takaful_portal_sponsor/static/img/trash.png" alt="cancel" /> الغاء
                                        < /a>
                                    ` } 
                                </td>
                            </tr>
                        `
                });
                $('.sponsorship_cancelation tbody').html(html);
                next = data.next_page;
                prev = (currentPage > 1) ? currentPage - 1 : null;
                currentPage = page;
            }
            else {
                console.log(data.msg);
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.log(textStatus + ': ' + errorThrown);
        }
    });
}


//cancelation request 

$(document).ready(function () {
    $('form#cancelation_form').on('submit', function (evt) {
        evt.preventDefault();
        var sponsorshipId = $('#sponsorship_id').val();
        var reasonId = $('#reason_id').val();
        var data = {
            sponsorship_id: sponsorshipId,
            reason_id: reasonId,
        };
        $.ajax({
            type: 'POST',
            url: '/portal/sponsor/sponsorships/cancel',
            data:data,
            dataType: 'json',
            success: function (data) {
                if (data.status) {
                    console.log(data);
                    $('.cancelation_feedback').show();
                    $('.cancelation_feedback').html(`<div class="alert alert-success">  ${data.msg}  </div>`);
                    setTimeout(function () {
                        $('.cancelation_feedback').hide();
                        // location.reload();
                    }, 3000);
                }

                else {
                    $('.cancelation_feedback').show();
                    $('.cancelation_feedback').html(`<div class="alert ui_error alert-danger">  ${data.msg}  </div>`);
                }
            },
            error: function (error) {
                console.log(error);
                $('.cancelation_feedback').show();
                $('.cancelation_feedback').html(`<div class="alert server_error alert-danger">${error.msg}</div>`);
                setTimeout(function () {
                    $('.cancelation_feedback').hide();
                }, 3000);
            }
        });
    }
    );
})


$(document).ready(function () {
    $('.need_sponsorship tbody').on('click', '#benefit_dtls', function (evt) {
        const userId = $(this).data("id");
        const userType = $(this).data("type")
        console.log(userId, userType);
        window.location.href = `/need_kafala_details?benefit_type=${userType}&benefit_id=${userId}`;
    })
})

$(document).ready(function () {
    loadData(1);
    sponsorshipsCancelation(1)
    function updateButtons(next, prev) {
        $('#benefits-next').attr('disabled', (next == null));
        $('#benefits-prev').attr('disabled', (prev == null));
    }

    $('#benefits-type').on('change', function () {
        loadData(1);
        sponsorshipsCancelation(1)
        let type = $(this).val();
        benefitType = type
        $('.kafalaty_table tbody tr').data("type", type)
    });
    $('#benefits-prev').click(function () {
        loadData(currentPage - 1);
        sponsorshipsCancelation(currentPage - 1);
        updateButtons(next, prev)

    });
    $('#benefits-next').click(function () {
        loadData(currentPage + 1);
        sponsorshipsCancelation(currentPage + 1);
        updateButtons(next, prev)
    });


    $('.sponsorship_cancelation tbody').on('click', '.cancel_link', function (e) {
        e.preventDefault();
        $('.cancelation_feedback').html('')
        $('#sponsorship_cancelation').modal('show');
        let sponsorship_id = $(this).data('id');
        console.log(sponsorship_id);
        $('#sponsorship_id').val(sponsorship_id)
    });
});