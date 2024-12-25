
$(document).ready(function () {
    var currentPage = 1;
    var benefitType = 'orphan'; // Default value
    var prev
    var next
    function loadNeedSponsorships(page) {
        $.ajax({
            url: '/portal/sys/benefits/page/' + page,
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
                            <tr class="expired">
                                <td> ${i + 1} </td>
                                <td data-type="${benefitType}" data-id="${element.id}" id="benefit_dtls"> ${element.first_name} </td>
                                <td> ${element.gender} </td>
                                <td> ${element.age} </td>
                                <td> ${element.city_id} </td>
                                <td> ${element.benefit_type} </td>
                                <td> ${element.benefit_needs_percent} % </td>
                                <td class="expired_td">
                                    <div class="d-flex align-items-center">
                                        <a data-id="${element.id}" href="#" class="sadad_link"> اكفلني الان </a>
                                    </div>
                                </td>
                            </tr>
                        `
                        $('#benefit_ids').append(`<option value=${element.id}> ${element.first_name} </option>`)
                    });
                    $('.need_sponsorship tbody').html(html);
                    next = data.next_page;
                    prev = (currentPage > 1) ? currentPage - 1 : null;
                    currentPage = page;

                }
                else {
                    console.log(data.msg);
                }
            },
            error: function (error) {
                console.log(error);
            }
        });
    }
    loadNeedSponsorships(1);
    function updateButtons(next, prev) {
        $('#benefits-next').attr('disabled', (next == null));
        $('#benefits-prev').attr('disabled', (prev == null));
    }

    $('#benefit-type').change(function () {
        benefitType = $(this).val();
        $('.financial_donation tbody tr #benefit_dtls').data("type", benefitType)
        loadNeedSponsorships(1);
    });
    $('#benefits-prev').click(function () {
        loadNeedSponsorships(currentPage - 1);
        updateButtons(next, prev)

    });
    $('#benefits-next').click(function () {
        loadNeedSponsorships(currentPage + 1);
        updateButtons(next, prev)
    });

})