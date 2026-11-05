/**
 * DevDiary Admin Panel Shared JavaScript (admin.js)
 * Consolidates sidebar toggle, toast dismiss, delete modal, image previews, and CKEditor integration.
 */

// Global reference for active CKEditor instances
let devDiaryEditors = {};

/**
 * Trigger styled Bootstrap 5 Delete Confirmation Modal
 * @param {string} actionUrl - Form POST action endpoint
 * @param {string} itemName - Name of item being deleted (e.g. post title, commenter name)
 * @param {string} itemType - Type of item (e.g. 'Article', 'Comment', 'Subscriber')
 */
function confirmDelete(actionUrl, itemName, itemType) {
    const form = document.getElementById('deleteConfirmForm');
    const title = document.getElementById('deleteModalTitle');
    const message = document.getElementById('deleteModalMessage');

    if (form && title && message) {
        form.action = actionUrl;
        title.innerText = 'Delete ' + (itemType || 'Item');
        message.innerHTML = 'Are you sure you want to delete ' + 
            (itemName ? '<strong>' + itemName + '</strong>' : 'this item') + 
            '?<br><span class="text-danger small">This action cannot be undone.</span>';

        const deleteModalEl = document.getElementById('deleteConfirmModal');
        if (deleteModalEl) {
            const deleteModal = bootstrap.Modal.getOrCreateInstance(deleteModalEl);
            deleteModal.show();
        }
    }
}

/**
 * Setup live image preview when user selects a file input
 * @param {string} inputId - ID of file input element
 * @param {string} containerId - ID of preview wrapper container
 * @param {string} imgId - ID of preview img tag
 */
function setupImagePreview(inputId, containerId, imgId) {
    const fileInput = document.getElementById(inputId);
    const container = document.getElementById(containerId);
    const previewImg = document.getElementById(imgId);

    if (fileInput && container && previewImg) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.src = e.target.result;
                    container.classList.remove('d-none');
                };
                reader.readAsDataURL(file);
            } else {
                container.classList.add('d-none');
            }
        });
    }
}

/**
 * Initialize CKEditor 5 on a textarea with full submit synchronization and reset support
 * @param {string} textareaId - Textarea selector or ID (e.g. '#editor')
 * @param {string} formSelector - Parent form selector
 */
function initCKEditor(textareaId, formSelector = 'form') {
    const textareaEl = document.querySelector(textareaId);
    if (!textareaEl || typeof ClassicEditor === 'undefined') {
        return;
    }

    ClassicEditor
        .create(textareaEl, {
            toolbar: [
                'heading', '|',
                'bold', 'italic', 'underline', 'link', '|',
                'bulletedList', 'numberedList', 'blockQuote', 'codeBlock', '|',
                'insertTable', '|',
                'undo', 'redo'
            ],
            heading: {
                options: [
                    { model: 'paragraph', title: 'Paragraph', class: 'ck-heading_paragraph' },
                    { model: 'heading1', view: 'h2', title: 'Heading 1', class: 'ck-heading_heading1' },
                    { model: 'heading2', view: 'h3', title: 'Heading 2', class: 'ck-heading_heading2' },
                    { model: 'heading3', view: 'h4', title: 'Heading 3', class: 'ck-heading_heading3' }
                ]
            }
        })
        .then(editor => {
            devDiaryEditors[textareaId] = editor;

            // Form Submit handler: Synchronize CKEditor HTML to textarea before sending
            const form = textareaEl.closest(formSelector);
            if (form) {
                form.addEventListener('submit', function(e) {
                    const editorData = editor.getData().trim();
                    textareaEl.value = editorData;

                    if (!editorData) {
                        e.preventDefault();
                        alert('Please enter article content before publishing.');
                        editor.editing.view.focus();
                    }
                });

                // Form Reset handler: Clear CKEditor content on reset button click
                form.addEventListener('reset', function() {
                    setTimeout(() => {
                        editor.setData('');
                    }, 50);
                });
            }
        })
        .catch(error => {
            console.error('CKEditor initialization error:', error);
        });
}

// Global UI Lifecycle Initializers
document.addEventListener('DOMContentLoaded', function() {
    // 1. Mobile Sidebar Toggle & Backdrop
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('adminSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');

    if (toggleBtn && sidebar && backdrop) {
        function openSidebar() {
            sidebar.classList.add('show');
            backdrop.classList.add('show');
        }

        function closeSidebar() {
            sidebar.classList.remove('show');
            backdrop.classList.remove('show');
        }

        toggleBtn.addEventListener('click', function() {
            if (sidebar.classList.contains('show')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });

        backdrop.addEventListener('click', closeSidebar);
    }

    // 2. Auto-hide Flash Notifications after 4 seconds
    document.querySelectorAll('.custom-admin-toast').forEach(function(toastEl) {
        setTimeout(function() {
            const bsToast = bootstrap.Toast.getOrCreateInstance(toastEl);
            if (bsToast) {
                bsToast.hide();
            }
        }, 4000);
    });
});

