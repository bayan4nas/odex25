// const city = document.getElementById("myCity")
// city.addEventListener('change', function handleChange(event) {
//     const cityVal = event.target.value;
//     console.log(cityVal);
// })
// $(document).ready(function () {
//     $('.submit button').click(function (e) {
//         e.preventDefault();
//         const countryCode = $('#basic-addon3').text();
//         const phone = $('#basic-url').val();
//         const number = countryCode + phone
//         const gender = $("input[type='radio'][name='gender']:checked").val();
//         // const api = 'https://jsonplaceholder.typicode.com/users';
//         // $.post(api, {

//         // })
//         console.log(number, gender);
//     })

//     // fetch(api)
//     //     .then(response => response.json())
//     //     .then(json => console.log(json))

// })


$(document).ready(function() {
    let count = $('.my_cart_quantity').html();
    $('#my_cart a').html(`<i class="mdi mdi-cart"></i> <sup class="my_cart_quantity label label-primary">${count}</sup>`);
    $('ul span.caret').remove();
    // $('ul#top_menu > li:last-child').remove();
    // $('ul#top_menu > li:last-child').remove();
})