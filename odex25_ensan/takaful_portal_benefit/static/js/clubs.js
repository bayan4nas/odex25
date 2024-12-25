$(document).ready(function () {

    let clubsApi = "/services/clubs";
    fetch(clubsApi)
        .then(response => response.json())
        .then(res => {
            allClubs = res.data;
            if (res.status && allClubs.length > 0) {
                allClubs.forEach((element, i) => {
                    let myClubs = element.clubs;
                    console.log(myClubs);
                    myClubs.forEach((club, i) => {
                        $('.clubs_row').append(
                            `
                            <div class="col-lg-6">
                                <div class="zakat_content">
                                    <h5> ${club.name} </h5>
                                    <ul class="list-unstyled p-0">
                                        <li>
                                            <img
                                                src="/takaful_portal_benefit/static/img/Icon awesome-info-circle.png"
                                                alt="info" />
                                            <span> ${club.description ? club.description : 'هنا يوجد وصف للنادي '} </span>
                                        </li>
                                        <li>
                                            <img
                                                src="/takaful_portal_benefit/static/img/Icon ionic-md-pricetag.png"
                                                alt="money" />
                                            <span> ${club.subscription_amount} </span>
                                        </li>
                                        <li>
                                            <img
                                                src="/takaful_portal_benefit/static/img/Icon awesome-volleyball-ball.png"
                                                alt="money" />
                                            <span> نوع النشاط (رياضي) </span>
                                        </li>
                                        <li>
                                            <img
                                                src="/takaful_portal_benefit/static/img/Icon material-date-range.png"
                                                alt="date" />
                                            <span> ${club.programs_type ? club.programs_type : 'نشاط اسبوعي'} </span>
                                        </li>
                                    </ul>
                                    <span data-id=${club.id}
                                        class="donation club_sub_link main_link"> اشترك 
                                        الان 
                                    </span>
                                </div>
                            </div>
                        `
                        )
                    })
                });
            } else {
                $('.clubs_row').append(`<div> لايوجد نوادي لعرضها هنا ! ..  </div>`)
            }
        });


    // club subscription 

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

    //set the club id 
    $('.clubs_row').on('click', '.club_sub_link', function () {
        $('.club_subscription_modal').modal('show');
        $("#club_id_input").val($(this).data('id'))
        console.log($("#club_id_input").val());
    });

    $('.club_sub_feedback').hide(); //hie the feedback div

    $('form#club_subscription_form').on('submit', function (evt) {
        evt.preventDefault();
        var form_data = $(this).serialize();
        console.log(form_data);
        var id = $("#club_id_input").val()
        var clubApi = `/services/club_subscription?id=${id}`;
        console.log(clubApi);
        $.ajax({
            url: clubApi,
            type: "POST",
            data: form_data,
            dataType: 'json',
            success: function (response) {
                if (response.status) {
                    $('.club_sub_feedback').show();
                    $(".club_sub_feedback").text(response.msg).addClass('alert alert-success')
                    setTimeout(function () {
                        $('.club_sub_feedback').hide();
                        location.reload();
                        // $('.zakat_modal').modal('hide');
                    }, 3000);
                } else {
                    $('.club_sub_feedback').show();
                    $(".club_sub_feedback").text(response.msg).addClass('alert alert-danger form_error')
                    setTimeout(function () {
                        $('.club_sub_feedback').hide();
                        // location.reload();
                    }, 3000);
                }
            },
            error: function (err) {
                $('.club_sub_feedback').show();
                $(".club_sub_feedback").text(err.msg).addClass('alert alert-danger server_error')
                setTimeout(function () {
                    $('.club_sub_feedback').hide();
                    // location.reload();
                }, 3000);
            }
        });
    });
}); 