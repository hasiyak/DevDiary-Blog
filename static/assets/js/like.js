// post.js - Single Post Page Like Logic
document.addEventListener("DOMContentLoaded", function() {
    const likeBtn = document.getElementById("likeBtn");
    const likeCount = document.getElementById("likeCount");
    const heartIcon = document.getElementById("heartIcon");

    if (likeBtn) {
        const postId = likeBtn.getAttribute("data-post-id");
        if (!postId) return;
        
        // 1. Check if user already liked this post in localStorage
        if (localStorage.getItem("liked_post_" + postId)) {
            likeBtn.style.backgroundColor = "#ff7518";
            likeBtn.style.color = "#ffffff";
            likeBtn.disabled = true;
            likeBtn.style.cursor = "default";
        }

        likeBtn.addEventListener("click", function() {
            if (localStorage.getItem("liked_post_" + postId) || likeBtn.disabled) {
                return;
            }

            likeBtn.disabled = true;

            // Send Like Request to Backend
            fetch(`/post/${postId}/like`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (likeCount) likeCount.innerText = data.likes;
                    
                    localStorage.setItem("liked_post_" + postId, "true");
                    
                    likeBtn.style.backgroundColor = "#ff7518";
                    likeBtn.style.color = "#ffffff";
                    likeBtn.style.cursor = "default";
                    likeBtn.classList.add("like-pop");
                    
                    if (heartIcon) {
                        heartIcon.classList.add("fa-beat");
                        setTimeout(() => {
                            heartIcon.classList.remove("fa-beat");
                            likeBtn.classList.remove("like-pop");
                        }, 1000);
                    }
                } else {
                    likeBtn.disabled = false;
                    console.error("Like update failed:", data.message);
                }
            })
            .catch(error => {
                likeBtn.disabled = false;
                console.error("Error updating likes:", error);
            });
        });
    }
});
