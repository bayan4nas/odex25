$(document).ready(function () {

    $('#category_id').on('change',function (){
        $(`#service_id`).prop('selectedIndex',-1);
        $(`#service_id option`).hide();
        let current = $('#category_id').find(':selected').val();
        console.log($('#category_id').find(':selected'));
        if(current !== ""){
            $('#service_id').removeAttr('disabled','disabled');
            $(`#service_id option[data-parent="${current}"]`).show();
        }else{
            $('#service_id').attr('disabled','disabled');
        }
    });

});