document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('recruitment5');
    const chooseFileButton = document.getElementById('choose_file_button');

    // When file input changes, update button text
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            chooseFileButton.textContent = 'Modify';
        } else {
            chooseFileButton.textContent = 'Choose File';
        }
    });

    // When choose file button is clicked, trigger file input click
    chooseFileButton.addEventListener('click', function() {
        fileInput.click();
    });

    // Prevent file input from being reset on click
    fileInput.addEventListener('click', function(event) {
        event.stopPropagation();
    });
});



$(document).ready(function () {
    // Open file dialog
    $('#uploadBtn').on('click', function () {
      $('#fileInput').click();
    });

    // When file is selected
    $('#fileInput').on('change', function () {
      const file = this.files[0];
      if (file) {
        $('#uploadBtn').hide();
        $('#file-name').text(file.name);
        $('#file-details').show();
      }
    });

    // Remove/reset file input
    $('#removeBtn').on('click', function () {
      $('#fileInput').val('');
      $('#file-details').hide();
      $('#file-name').text('');
      $('#uploadBtn').show();
    });
  });

