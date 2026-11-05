document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("newsletterForm");
    const emailInput = document.getElementById("newsletterEmail");
    const msgDiv = document.getElementById("newsletterMsg");

    if (form) {
        form.addEventListener("submit", function(e) {
            e.preventDefault(); // Prevent default page reload on submit
            const email = emailInput ? emailInput.value.trim() : '';

            if (!email) return;

            // Send subscription request to backend /subscribe endpoint
            fetch('/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email })
            })
            .then(response => response.json())
            .then(data => {
                if (!msgDiv) return;

                msgDiv.style.display = 'block';
                msgDiv.innerText = data.message;
                
                if (data.success) {
                    msgDiv.style.color = '#ff7518'; // Highlight with theme orange on success
                    if (emailInput) emailInput.value = ''; // Clear input field
                } else {
                    msgDiv.style.color = '#dc3545'; // Highlight with red on error
                }
                
                // Automatically hide message after 5 seconds
                setTimeout(() => {
                    msgDiv.style.display = 'none';
                }, 5000);
            })
            .catch(error => {
                console.error('Newsletter Error:', error);
            });
        });
    }
});
