// Toast Notification Function
function showToast(message, type) {
    const toast = document.getElementById('customToast');
    const content = document.getElementById('toastContent');
    const text = document.getElementById('toastText');
    const icon = document.getElementById('toastIcon');

    if (!toast || !content || !text || !icon) return;

    text.innerText = message;
    
    if (type === 'error') {
        content.style.backgroundColor = '#ef4444'; // Red
        icon.className = 'fas fa-exclamation-circle me-3 fs-4';
    } else {
        content.style.backgroundColor = '#10b981'; // Green
        icon.className = 'fas fa-check-circle me-3 fs-4';
    }

    toast.style.visibility = 'visible';
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(0)';

    setTimeout(hideToast, 4500);
}

function hideToast() {
    const toast = document.getElementById('customToast');
    if (!toast) return;
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => { 
        toast.style.visibility = 'hidden'; 
    }, 400);
}

document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("contactForm");
    if (!form) return; 

    const nameInput = document.getElementById("nameInput");
    const emailInput = document.getElementById("emailInput");
    const subjectInput = document.getElementById("subjectInput");
    const messageInput = document.getElementById("messageInput");
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    function validateInput(input, isValid) {
        if (!input) return;
        if (isValid) {
            input.classList.remove("is-invalid");
            input.classList.add("is-valid");
        } else {
            input.classList.remove("is-valid");
            input.classList.add("is-invalid");
        }
    }

    if (nameInput) {
        nameInput.addEventListener("input", () => {
            validateInput(nameInput, nameInput.value.trim().length >= 3);
        });
    }

    if (emailInput) {
        emailInput.addEventListener("input", () => {
            validateInput(emailInput, emailRegex.test(emailInput.value.trim()));
        });
    }

    if (subjectInput) {
        subjectInput.addEventListener("input", () => {
            // Subject is optional or at least 3 chars if filled
            const val = subjectInput.value.trim();
            validateInput(subjectInput, val.length === 0 || val.length >= 3);
        });
    }

    if (messageInput) {
        messageInput.addEventListener("input", () => {
            validateInput(messageInput, messageInput.value.trim().length >= 10);
        });
    }

    form.addEventListener("submit", function(event) {
        const isNameValid = nameInput ? nameInput.value.trim().length >= 3 : false;
        const isEmailValid = emailInput ? emailRegex.test(emailInput.value.trim()) : false;
        const subjectVal = subjectInput ? subjectInput.value.trim() : "";
        const isSubjectValid = subjectVal.length === 0 || subjectVal.length >= 3;
        const isMessageValid = messageInput ? messageInput.value.trim().length >= 10 : false;

        validateInput(nameInput, isNameValid);
        validateInput(emailInput, isEmailValid);
        if (subjectInput && subjectVal.length > 0) {
            validateInput(subjectInput, isSubjectValid);
        }
        validateInput(messageInput, isMessageValid);

        if (!isNameValid || !isEmailValid || !isMessageValid || !isSubjectValid) {
            event.preventDefault();
            showToast("Please check the highlighted fields and try again.", "error");
        }
    });
});
