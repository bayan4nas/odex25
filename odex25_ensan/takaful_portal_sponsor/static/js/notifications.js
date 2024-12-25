var currentPage = 1;
var next
var prev


const urlSearchParams = new URLSearchParams(window.location.search);
var is_read = urlSearchParams.get("is_read");

if(is_read =='no'){
    $("#unread_toggler").prop('checked', true);
}

function updateButtons(nxt, prv) {
    $('#benefits-next').attr('disabled', (nxt == null));
    $('#benefits-prev').attr('disabled', (prv == null));
}

//load read notifiacrions
if (is_read == 'yes') {
    function loadNotifications(page) {
        $.ajax({
            url: `/portal/sponsor/notifications/page/${page}?is_read=yes`,
            type: 'GET',
            dataType: 'json',
            success: function (data) {
                console.log(data);
                notif = data.results;
                let myPage = data.next_page;
                console.log(myPage);
                var html = '';
                if (data.status) {
                    notif.forEach((element, i) => {
                        html +=
                            `
                            <a style="display:block" href="/notifications_details?id=${element.id}" class="single_notification">
                                <h5>
                                    ${element.title}
                                </h5>
                                <p>
                                    ${element.body}
                                </p>
                                <span>
                                    ${element.sent_on}
                                </span>
                            </a>
                            `
                    });
                    $('.all_notifs').html(html);

                    next = data.next_page;
                    prev = (currentPage > 1) ? currentPage - 1 : null;
                    currentPage = page;
                    console.log(next, prev);
                    $('#notif-next').attr('disabled', (next == null));
                    $('#notif-prev').attr('disabled', (prev == null));
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
}
//load all notifications
else if (is_read == 'no') {

    function loadNotifications(page) {
        $.ajax({
            url: `/portal/sponsor/notifications/page/${page}?is_read=no`,
            type: 'GET',
            dataType: 'json',
            success: function (data) {
                console.log(data);
                notif = data.results;
                let myPage = data.next_page;
                console.log(myPage);
                var html = '';
                if (data.status) {
                    notif.forEach((element, i) => {
                        html +=
                            `
                            <a style="display:block" href="/notifications_details?id=${element.id}" class="single_notification">
                                <h5>
                                    ${element.title}
                                </h5>
                                <p>
                                    ${element.body}
                                </p>
                                <span>
                                    ${element.sent_on}
                                </span>
                            </a>
                            `
                    });
                    $('.all_notifs').html(html);

                    next = data.next_page;
                    prev = (currentPage > 1) ? currentPage - 1 : null;
                    currentPage = page;
                    console.log(next, prev);
                    $('#notif-next').attr('disabled', (next == null));
                    $('#notif-prev').attr('disabled', (prev == null));
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

} else {
    function loadNotifications(page) {
        $.ajax({
            url: `/portal/sponsor/notifications/page/${page}`,
            type: 'GET',
            dataType: 'json',
            success: function (data) {
                console.log(data);
                notif = data.results;
                let myPage = data.next_page;
                console.log(myPage);
                var html = '';
                if (data.status) {
                    notif.forEach((element, i) => {
                        html +=
                            `
                            <a style="display:block" href="/notifications_details?id=${element.id}"  class="single_notification">
                                <h5>
                                    ${element.title}
                                </h5>
                                <p>
                                    ${element.body}
                                </p>
                                <span>
                                    ${element.sent_on}
                                </span>
                            </a>
                            `
                    });
                    $('.all_notifs').html(html);

                    next = data.next_page;
                    prev = (currentPage > 1) ? currentPage - 1 : null;
                    currentPage = page;
                    console.log(next, prev);
                    $('#notif-next').attr('disabled', (next == null));
                    $('#notif-prev').attr('disabled', (prev == null));
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
}




$(document).ready(function () {
    loadNotifications(1);
    $('#notif-prev').click(function () {
        loadNotifications(currentPage - 1);
        updateButtons(next, prev)
    });
    $('#notif-next').click(function () {
        loadNotifications(currentPage + 1);
        updateButtons(next, prev)
    });
});