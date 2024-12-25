$(document).ready(function () {
    var currentPage = 1;
    var prev
    var next


    function paymentsHandler(page) {
        $.ajax({
            url: '/portal/sponsor/payments/page/' + page,
            type: 'GET',
            dataType: 'json',
            success: function (data) {
                results = data.results;
                nextPage = data.next_page;
                console.log(nextPage);
                console.log(data);
                var html = '';
                if (data.status) {
                    results.forEach((element, i) => {
                        html +=
                            `
                            <tr data-id="${element.id}" class="expired">
                                <td> ${i + 1} </td>
                                <td> ${element.name} </td>
                                <td> ${element.title} </td>
                                <td> ${element.date} </td>
                                <td> ${element.amount} </td>
                                <td class="expired_td">
                                    <div class="d-flex align-items-center justify-content-center">
                                        <span class="sadad_link m-0 payment_done d-block w-100">   تم السداد </span>
                                    </div>
                                </td>
                            </tr>
                        `
                    });
                    $('.payments_table tbody').html(html);

                    currentPage = page;
                    next = data.next_page;
                    prev = (currentPage > 1) ? currentPage - 1 : null;
                    updateButtons(next, prev);
                }
                else {
                    $('.payments_table').hide();
                    $('.empty_payments').text('لايوجد مدفوعات لعرضها ')
                }
            },
            error: function (err) {
                $('.empty_payments').text(err.msg)
            }
        });
    }


    function arreasHandler(page) {
        $.ajax({
            url: '/portal/sponsor/arrears/page/' + page,
            type: 'GET',
            dataType: 'json',
            success: function (data) {
                results = data.results;
                nextPage = data.next_page;
                console.log(nextPage);
                console.log(data);
                var html = '';
                if (data.status) {
                    results.forEach((element, i) => {
                        html +=
                            `
                            <tr data-id="${element.id}" class="expired">
                                <td> ${i + 1} </td>
                                <td> ${element.code} </td>
                                <td> ${element.next_due_date} </td>
                                <td> ${element.contribution_value} </td>
                                <td> ${element.due_days} </td>
                                <td class="expired_td">
                                    <div
                                        class="d-flex align-items-center justify-content-center">
                                        <a href="#"
                                            class="sadad_link m-0 payment_sadad d-block w-100">
                                            سداد </a>
                                        <a href="#"
                                            class="sadad_link payment_cancel d-block w-100">
                                            الغاء </a>
                                    </div>
                                </td>
                            </tr>
                        `
                    });
                    $('.arreas_table tbody').html(html);
                    currentPage = page;
                    console.log(currentPage);
                    next = data.next_page;
                    console.log('next is' + next);
                    prev = (currentPage > 1) ? currentPage - 1 : null;
                    updateButtons(next, prev);
                }
                else {
                    $('.arreas_table').hide();
                    $('.empty_arreas').text('لايوجد مدفوعات لعرضها ')
                }
            },
            error: function (err) {
                $('.empty_arreas').text(err.msg)
            }
        });
    }

    paymentsHandler(currentPage);
    arreasHandler(currentPage);

    function updateButtons(next, prev) {
        $('#payments_next').prop('disabled', (next === null));
        $('#payments_prev').prop('disabled', (currentPage === 1));
    }

    // Button click event handlers
    $('#payments_next').click(function () {
        if (next) {
            paymentsHandler(currentPage + 1);
            arreasHandler(currentPage + 1);
        }
    });
    $('#payments_prev').click(function () {
        paymentsHandler(currentPage - 1);
        arreasHandler(currentPage - 1);

    });

})