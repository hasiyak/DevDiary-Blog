document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("searchInput");
    const searchResults = document.getElementById("searchResults");

    if (searchInput && searchResults) {
        let debounceTimer = null;

        function escapeHtml(text) {
            const div = document.createElement("div");
            div.textContent = text;
            return div.innerHTML;
        }

        searchInput.addEventListener("input", function() {
            clearTimeout(debounceTimer);
            const query = this.value.trim();

            if (query.length < 2) {
                searchResults.style.display = "none";
                searchResults.innerHTML = "";
                return;
            }

            // Debounce request by 250ms for performance
            debounceTimer = setTimeout(() => {
                fetch(`/api/search?q=${encodeURIComponent(query)}`)
                    .then(response => {
                        if (!response.ok) throw new Error("Network response was not ok");
                        return response.json();
                    })
                    .then(data => {
                        searchResults.innerHTML = "";
                        if (Array.isArray(data) && data.length > 0) {
                            data.forEach(post => {
                                const li = document.createElement("li");
                                const safeTitle = escapeHtml(post.title);
                                li.innerHTML = `<a class="dropdown-item py-2 px-3 border-bottom text-wrap d-flex align-items-center" href="/post/${post.id}">
                                    <i class="fas fa-file-alt text-muted me-2 small"></i>
                                    <span>${safeTitle}</span>
                                </a>`;
                                searchResults.appendChild(li);
                            });
                            searchResults.style.display = "block";
                        } else {
                            searchResults.innerHTML = `<li class="dropdown-item py-2 px-3 text-muted small"><i class="fas fa-info-circle me-2"></i>No articles found</li>`;
                            searchResults.style.display = "block";
                        }
                    })
                    .catch(error => {
                        console.error("Error fetching search results:", error);
                        searchResults.style.display = "none";
                    });
            }, 250);
        });

        // Close dropdown on click outside
        document.addEventListener("click", function(event) {
            if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
                searchResults.style.display = "none";
            }
        });

        // Close on Escape key
        document.addEventListener("keydown", function(event) {
            if (event.key === "Escape") {
                searchResults.style.display = "none";
            }
        });
    }
});
