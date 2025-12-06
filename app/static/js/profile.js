let comments = window.profileComments || []; 
let index = 0;

const displayBox = document.getElementById("comment-display");
const prevBtn = document.getElementById("prev-btn");
const nextBtn = document.getElementById("next-btn");

function showComment() {
    if (!comments.length) {
        displayBox.innerHTML = "<em>No comments yet.</em>";
        return;
    }

    const c = comments[index];
    displayBox.innerHTML = `
        <p>${c.text}</p>
        <div class="commenter">— ${c.commenter}</div>
    `;
}

prevBtn.addEventListener("click", () => {
    if (comments.length) {
        index = (index - 1 + comments.length) % comments.length;
        showComment();
    }
});

nextBtn.addEventListener("click", () => {
    if (comments.length) {
        index = (index + 1) % comments.length;
        showComment();
    }
});

showComment();
