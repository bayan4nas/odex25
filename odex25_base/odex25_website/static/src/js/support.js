$(document).ready(function () {
    var addFileInputButton = document.getElementById('add-file-input');

    if (addFileInputButton) {
        addFileInputButton.addEventListener('click', function(e) {
            e.preventDefault();

            var addAnotherAttachment = document.getElementById('file-input-container');

            var wrapper = document.createElement('div');
            wrapper.classList.add('attachment-wrapper');

            var newInput = document.createElement('input');
            newInput.type = 'file';
            newInput.name = 'attachments[]';

            var deleteButton = document.createElement('button');
            deleteButton.textContent = 'X';
            deleteButton.classList.add('delete-button');
            deleteButton.type = 'button'; 

            deleteButton.addEventListener('click', function() {
                wrapper.remove();
            });

            wrapper.appendChild(newInput);
            wrapper.appendChild(deleteButton);

            addAnotherAttachment.insertBefore(wrapper, this);
        });
    } else {
        console.error("The 'add-file-input' element does not exist in the DOM.");
    }
});
