const config = window.RESUME_CONFIG;
const documentId = config.documentId;
let reviews = config.reviews || []; // array of { reviewer_id, reviewer_name, highlights }
let currentReviewIndex = 0;

pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
const PDF_SCALE = 1.5;
let pdfDocument = null;

// helper to create highlight rectangles
function createHighlightRect(bounds, highlightId = null) {
    const rect = document.createElement("div");
    rect.className = "highlight-rect";
    rect.style.left = bounds.left + "px";
    rect.style.top = bounds.top + "px";
    rect.style.width = bounds.width + "px";
    rect.style.height = bounds.height + "px";

    if (highlightId) {
        rect.setAttribute("data-highlight-id", highlightId);
        rect.style.cursor = "pointer";
        rect.addEventListener("click", (e) => {
            e.stopPropagation();
            selectCommentById(highlightId);
        });
    }

    return rect;
}

// render highlights for a specific page using current review data
function renderHighlights(pageNum, viewport, highlightLayer) {
    highlightLayer.innerHTML = "";

    const currentReview = reviews[currentReviewIndex];
    if (!currentReview) return;

    const highlights = currentReview.highlights || {};
    const pageKey = pageNum.toString();

    if (highlights[pageKey] && highlights[pageKey].length > 0) {
        highlights[pageKey].forEach((highlight) => {
            if (highlight.rects && highlight.rects.length > 0) {
                highlight.rects.forEach((rectData) => {
                    const startPdf = [rectData.x, rectData.y];
                    const endPdf = [
                        rectData.x + rectData.width,
                        rectData.y - rectData.height,
                    ];

                    const startViewport = viewport.convertToViewportPoint(
                        startPdf[0],
                        startPdf[1]
                    );
                    const endViewport = viewport.convertToViewportPoint(
                        endPdf[0],
                        endPdf[1]
                    );

                    const bounds = {
                        left: Math.min(startViewport[0], endViewport[0]),
                        top: Math.min(startViewport[1], endViewport[1]),
                        width: Math.abs(endViewport[0] - startViewport[0]),
                        height: Math.abs(endViewport[1] - startViewport[1]),
                    };

                    const rect = createHighlightRect(bounds, highlight.id);
                    highlightLayer.appendChild(rect);
                });
            }
        });
    }
}

// re-render highlights on all visible pages
function updateAllHighlights() {
    const pages = document.querySelectorAll(".page-container");
    pages.forEach(async (pageDiv, index) => {
        const pageNum = index + 1;
        const highlightLayer = pageDiv.querySelector(".highlight-layer");
        const pdfPage = await pdfDocument.getPage(pageNum);
        const viewport = pdfPage.getViewport({ scale: PDF_SCALE });
        renderHighlights(pageNum, viewport, highlightLayer);
    });
}

// render a single PDF page structure
async function renderPage(pageNum, pdfPage, container) {
    const viewport = pdfPage.getViewport({ scale: PDF_SCALE });

    const pageDiv = document.createElement("div");
    pageDiv.className = "page-container";
    pageDiv.style.width = viewport.width + "px";
    pageDiv.style.height = viewport.height + "px";

    const canvasWrapper = document.createElement("div");
    canvasWrapper.className = "canvas-wrapper";
    canvasWrapper.style.width = viewport.width + "px";
    canvasWrapper.style.height = viewport.height + "px";

    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const textLayer = document.createElement("div");
    textLayer.className = "textLayer";
    textLayer.style.width = viewport.width + "px";
    textLayer.style.height = viewport.height + "px";
    textLayer.style.setProperty("--scale-factor", PDF_SCALE);

    const highlightLayer = document.createElement("div");
    highlightLayer.className = "highlight-layer";

    canvasWrapper.appendChild(canvas);
    canvasWrapper.appendChild(textLayer);
    canvasWrapper.appendChild(highlightLayer);
    pageDiv.appendChild(canvasWrapper);
    container.appendChild(pageDiv);

    const renderContext = {
        canvasContext: context,
        viewport: viewport,
    };
    await pdfPage.render(renderContext).promise;

    // initial highlight render
    renderHighlights(pageNum, viewport, highlightLayer);

    return pageDiv;
}

// main PDF render
async function render() {
    pdfDocument = await pdfjsLib.getDocument({
        url: documentId,
        cMapUrl: "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/",
        cMapPacked: true,
    }).promise;

    const viewer = document.getElementById("viewer");
    viewer.innerHTML = "";

    const numPages = pdfDocument.numPages;
    const renderPromises = [];

    for (let pageNum = 1; pageNum <= numPages; pageNum++) {
        const pdfPage = await pdfDocument.getPage(pageNum);
        renderPromises.push(renderPage(pageNum, pdfPage, viewer));
    }

    await Promise.all(renderPromises);

    // initial UI state
    updateReviewerDisplay();
}

// update the UI for the current reviewer
function updateReviewerDisplay() {
    const reviewerNameEl = document.getElementById("reviewer-name");
    const prevBtn = document.getElementById("prev-btn");
    const nextBtn = document.getElementById("next-btn");

    if (reviews.length === 0) {
        reviewerNameEl.textContent = "No Reviews";
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        renderComments(); // will clear comments
        updateAllHighlights(); // will clear highlights
        return;
    }

    const currentReview = reviews[currentReviewIndex];
    reviewerNameEl.textContent = currentReview.reviewer_name || "Anonymous";

    // update buttons
    prevBtn.disabled = currentReviewIndex === 0;
    nextBtn.disabled = currentReviewIndex === reviews.length - 1;

    // update content
    renderComments();
    updateAllHighlights();
}

// render comments sidebar
function renderComments() {
    const commentsList = document.getElementById("comments-list");
    commentsList.innerHTML = "";

    const currentReview = reviews[currentReviewIndex];
    if (!currentReview) {
        commentsList.innerHTML = "<p>No comments available.</p>";
        return;
    }

    const highlights = currentReview.highlights || {};
    let allComments = [];

    Object.keys(highlights).forEach((pageKey) => {
        const pageHighlights = highlights[pageKey];
        if (Array.isArray(pageHighlights)) {
            pageHighlights.forEach((highlight, index) => {
                if (highlight && highlight.comment && highlight.comment.trim() !== "") {
                    allComments.push({
                        pageNum: parseInt(pageKey),
                        highlight: highlight,
                    });
                }
            });
        }
    });

    allComments.sort((a, b) => {
        if (a.pageNum !== b.pageNum) return a.pageNum - b.pageNum;
        const aTop = a.highlight.rects[0]?.y || 0;
        const bTop = b.highlight.rects[0]?.y || 0;
        return bTop - aTop;
    });

    if (allComments.length === 0) {
        commentsList.innerHTML = "<p>No comments yet.</p>";
        return;
    }

    allComments.forEach(({ pageNum, highlight }) => {
        const commentItem = document.createElement("div");
        commentItem.className = "comment-item";
        commentItem.setAttribute("data-highlight-id", highlight.id);

        const commentText = document.createElement("div");
        commentText.className = "comment-text";
        commentText.textContent = highlight.comment;
        commentItem.appendChild(commentText);

        commentItem.addEventListener("click", () => {
            selectComment(commentItem, highlight.id);
        });

        commentsList.appendChild(commentItem);
    });
}

function selectComment(commentElement, highlightId) {
    const commentsList = document.getElementById("comments-list");
    const allComments = commentsList.querySelectorAll(".comment-item");
    allComments.forEach((item) => item.classList.remove("selected"));
    commentElement.classList.add("selected");
    highlightYellowBoxes(highlightId);
}

function selectCommentById(highlightId) {
    const commentsList = document.getElementById("comments-list");
    const allComments = commentsList.querySelectorAll(".comment-item");
    allComments.forEach((item) => item.classList.remove("selected"));

    let targetItem = null;
    allComments.forEach((item) => {
        if (item.getAttribute("data-highlight-id") === highlightId) {
            item.classList.add("selected");
            targetItem = item;
        }
    });

    if (targetItem) {
        targetItem.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
    highlightYellowBoxes(highlightId);
}

function highlightYellowBoxes(highlightId) {
    const allHighlightRects = document.querySelectorAll(".highlight-rect");
    allHighlightRects.forEach((rect) => rect.classList.remove("active"));
    allHighlightRects.forEach((rect) => {
        if (rect.getAttribute("data-highlight-id") === highlightId) {
            rect.classList.add("active");
        }
    });
}

// event Listeners for Buttons
document.getElementById("prev-btn").addEventListener("click", () => {
    if (currentReviewIndex > 0) {
        currentReviewIndex--;
        updateReviewerDisplay();
    }
});

document.getElementById("next-btn").addEventListener("click", () => {
    if (currentReviewIndex < reviews.length - 1) {
        currentReviewIndex++;
        updateReviewerDisplay();
    }
});

render();