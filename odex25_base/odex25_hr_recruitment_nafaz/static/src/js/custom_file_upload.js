$(document).ready(function () {
    // Open file dialog
    $('#uploadBtn').on('click', function () {
      $('#recruitment5').click();
    });

    // When file is selected
    $('#recruitment5').on('change', function () {
      const file = this.files[0];
      if (file) {
        $('#uploadBtn').hide();
        $('#file-name').text(file.name);
        $('#file-details').addClass("show");
      }else{
        $('#file-details').removeClass("show");
      }
    });

    // Remove/reset file input
    $('#removeBtn').on('click', function () {
      $('#recruitment5').val('');
      $('#file-details').removeClass("show");
      $('#file-name').text('');
      $('#uploadBtn').show(); 
    });
  });

