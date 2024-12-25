const urlSearchParams = new URLSearchParams(window.location.search);
var myId = urlSearchParams.get("id");

$.ajax({
    url: `/portal/sponsor/notify/read/${myId}`,
    type: 'GET',
    dataType: 'json',
    success: function (data) {
        console.log(data);
        notif_details = data.notification;
        var html = '';
        if (data.status) {
            html +=
                `
                    <div style="margin-bottom: 24px" class="noti_content">
                        <div class="date" id="rere">
                            ${notif_details.sent_on}
                        </div>
                        <div class="single_notification">
                            <h5> ${notif_details.title}  </h5>
                            <p>
                            ${notif_details.body} 
                            </p>
                            <div class="dropdown">
                                <button class="dropdown-toggle" type="button" id="dropdownMenu1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
                                        <img src="/takaful_portal_sponsor/static/img/noti_options.png" alt="noti_options" />
                                </button>
                                <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
                                    <li>
                                        <span data-id=${notif_details.id} class="delete_noti">
                                        حذف
                                        </span>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="delete_feedback"></div>
                    `
            $('.notifications.details .wrapper').html(html);
        }
        else {
            console.log(data.msg);
        }
    },
    error: function (jqXHR, textStatus, errorThrown) {
        console.log(textStatus + ': ' + errorThrown);
    }
});

$(".notifications.details").on("click", ".delete_noti", () => {
    $.ajax({
        url: `/portal/sponsor/notify/delete/${myId}`,
        type: 'GET',
        dataType: 'json',
        success: function (data) {
            console.log(data);
            var message = data.msg ;
            if (data.status) {
                $('.delete_feedback').append(`<span class="alert alert-success"> ${message} </span>`);
                setTimeout(function () {
                    window.location.href = `/notifications`;
                }, 3000);
            }
            else {
                $('.delete_feedback').append(`<span class="alert  alert-danger"> ${message} </span>`);
            }
        },
        error: function (err) {
            $('.delete_feedback').append(`<span class="alert alert-danger"> ${err.msg} </span>`);
        }
    });
})