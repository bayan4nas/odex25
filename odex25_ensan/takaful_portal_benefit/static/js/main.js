// const city = document.getElementById("myCity")
// city.addEventListener('change', function handleChange(event) {
//     const cityVal = event.target.value;
//     console.log(cityVal);
// })
$(document).ready(function () {
    $('#table_id').DataTable({
        responsive: true,
        language: {
            'paginate': {
                'previous': '<img src="/takaful_portal_benefit/static/img/prev.png" alt="prev" />',
                'next': '<img src="/takaful_portal_benefit/static/img/next.png" alt="next" />'
            }
        }
    });

    $(".trigger_group_guarantee_modal").click(function (e) {
        e.preventDefault();
        $('.group_guarantee_modal').modal('show')
    })

    // fetch(api)
    //     .then(response => response.json())
    //     .then(json => console.log(json))


    //cities integration 

    let citiesApi = '/portal/cities';
    fetch(citiesApi)
        .then(response => response.json())
        .then(res => {
            data = res.cities;
            data.forEach((city, i) => {
                $("#city_id").append(`<option value="${city[0]}">${city[1]}</option>`);
            })
        })
    // banks
    let banks = "/api/banks";
    fetch(banks).then(res => res.json()).then(banks => {
        allBanks = banks.results;
        allBanks.forEach((bank, i) => {
            $('#bank_id').append(`<option value=${bank.id}> ${bank.name} </option>`)
        });
    })

    //states 

    let statesApi = '/portal/states';
    fetch(statesApi)
        .then(response => response.json())
        .then(res => {
            data = res.states;
            data.forEach((state, i) => {
                $("#state_id").append(`<option value="${state[0]}">${state[1]}</option>`);
            })
        })


})


$(document).ready(function () {
    $('input[type="file"]').change(function () {
        var filename = $(this).val().split('\\').pop();
        $(this).closest('.attach_wrapper').find('input[type="text"]').val(filename);
    });
});
