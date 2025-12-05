const documentId = '/static/pdf/jakes-resume.pdf';
const STORAGE_KEY = 'pdf-highlights';

pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

let pdfDocument = null;
let highlights = loadHighlights();
let currentTemporaryHighlight = null; // Preview highlight shown before user confirms save/cancel
let currentHighlightData = null;

function loadHighlights() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? JSON.parse(stored) : {};
    } catch (e) {
        console.warn('Failed to load highlights:', e);
        return {};
    }
}

function saveHighlights() {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(highlights));
    } catch (e) {
        console.warn('Failed to save highlights:', e);
    }
}

function generateHighlightId() {
    return 'hl_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Extracts bounding boxes for selected text spans using Range.getClientRects().
 * getClientRects() automatically accounts for CSS transforms that PDF.js applies.
 */
function getSelectedTextSpans(selection, highlightLayer) {
    if (selection.rangeCount === 0) {
        return [];
    }

    const range = selection.getRangeAt(0);
    const highlightLayerRect = highlightLayer.getBoundingClientRect();
    const spans = [];

    const clientRects = range.getClientRects();

    for (let i = 0; i < clientRects.length; i++) {
        const rect = clientRects[i];

        const relativeRect = {
            left: rect.left - highlightLayerRect.left,
            top: rect.top - highlightLayerRect.top,
            width: rect.width,
            height: rect.height
        };

        if (relativeRect.width > 0 && relativeRect.height > 0) {
            spans.push(relativeRect);
        }
    }

    return spans;
}

function createHighlightRect(bounds, isTemporary = false) {
    const rect = document.createElement('div');
    rect.className = 'highlight-rect' + (isTemporary ? ' temporary' : '');
    rect.style.left = bounds.left + 'px';
    rect.style.top = bounds.top + 'px';
    rect.style.width = bounds.width + 'px';
    rect.style.height = bounds.height + 'px';
    return rect;
}

/**
 * Renders highlights for a page. Handles both saved highlights (from localStorage) and temporary
 * highlights (preview before save/cancel). The includeTemporary flag allows us to show the preview
 * while keeping saved highlights visible, then remove it after the user decides to save or cancel.
 * 
 * Coordinates are stored in PDF space (bottom-left origin) but must be converted to viewport space
 * (top-left origin) for rendering.
 */
function renderHighlights(pageNum, viewport, highlightLayer, includeTemporary = false) {
    // When including temporary, only remove permanent highlights to avoid flicker
    if (!includeTemporary || !currentTemporaryHighlight) {
        highlightLayer.innerHTML = '';
    } else {
        const allRects = highlightLayer.querySelectorAll('.highlight-rect');
        allRects.forEach(rect => {
            if (!rect.classList.contains('temporary')) {
                rect.remove();
            }
        });
    }

    const pageKey = pageNum.toString();

    if (highlights[pageKey] && highlights[pageKey].length > 0) {
        highlights[pageKey].forEach(highlight => {
            if (highlight.rects && highlight.rects.length > 0) {
                highlight.rects.forEach(rectData => {
                    const startPdf = [rectData.x, rectData.y];
                    const endPdf = [rectData.x + rectData.width, rectData.y - rectData.height];

                    const startViewport = viewport.convertToViewportPoint(startPdf[0], startPdf[1]);
                    const endViewport = viewport.convertToViewportPoint(endPdf[0], endPdf[1]);

                    const bounds = {
                        left: Math.min(startViewport[0], endViewport[0]),
                        top: Math.min(startViewport[1], endViewport[1]),
                        width: Math.abs(endViewport[0] - startViewport[0]),
                        height: Math.abs(endViewport[1] - startViewport[1])
                    };

                    const rect = createHighlightRect(bounds, false);
                    highlightLayer.appendChild(rect);
                });
            }
        });
    }

    if (includeTemporary && currentTemporaryHighlight) {
        currentTemporaryHighlight.rects.forEach(rectData => {
            const startPdf = [rectData.x, rectData.y];
            const endPdf = [rectData.x + rectData.width, rectData.y - rectData.height];

            const startViewport = viewport.convertToViewportPoint(startPdf[0], startPdf[1]);
            const endViewport = viewport.convertToViewportPoint(endPdf[0], endPdf[1]);

            const bounds = {
                left: Math.min(startViewport[0], endViewport[0]),
                top: Math.min(startViewport[1], endViewport[1]),
                width: Math.abs(endViewport[0] - startViewport[0]),
                height: Math.abs(endViewport[1] - startViewport[1])
            };

            const rect = createHighlightRect(bounds, true);
            highlightLayer.appendChild(rect);
        });
    }
}

/**
 * Shows the confirmation popup when text is selected. Buttons are cloned to remove old event
 * listeners and prevent duplicate handlers. The delay on click-outside handler prevents immediate
 * dismissal when the popup first appears (since the mouseup event that triggered selection would
 * also trigger click-outside).
 */
function showHighlightPopup(selectedText, pageNum, viewport, highlightLayer) {
    const popup = document.getElementById('highlight-popup');
    const textDisplay = document.getElementById('popup-selected-text');
    const commentInput = document.getElementById('popup-comment-input');
    const saveBtn = document.getElementById('popup-save-btn');
    const cancelBtn = document.getElementById('popup-cancel-btn');

    textDisplay.textContent = selectedText;
    commentInput.value = '';
    commentInput.classList.remove('error');

    const popupRect = popup.getBoundingClientRect();
    popup.style.left = (window.innerWidth / 2 - popupRect.width / 2) + 'px';
    popup.style.top = (window.innerHeight / 2 - popupRect.height / 2) + 'px';

    popup.classList.add('visible');

    // Focus on comment input for better UX
    setTimeout(() => {
        commentInput.focus();
    }, 100);

    // Clone buttons to remove old event listeners (prevents duplicate handlers)
    const newSaveBtn = saveBtn.cloneNode(true);
    const newCancelBtn = cancelBtn.cloneNode(true);
    saveBtn.parentNode.replaceChild(newSaveBtn, saveBtn);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);

    // Function to validate and update save button state
    const updateSaveButtonState = () => {
        const commentValue = commentInput.value.trim();
        const isValid = commentValue.length > 0;
        newSaveBtn.disabled = !isValid;
        if (isValid) {
            newSaveBtn.classList.remove('disabled');
        } else {
            newSaveBtn.classList.add('disabled');
        }
    };

    // Initially disable save button
    newSaveBtn.disabled = true;
    newSaveBtn.classList.add('disabled');

    // Validate on input
    commentInput.addEventListener('input', updateSaveButtonState);

    const saveHandler = () => {
        const commentValue = commentInput.value.trim();
        if (commentValue.length === 0) {
            commentInput.focus();
            commentInput.classList.add('error');
            return;
        }
        commentInput.classList.remove('error');
        if (currentTemporaryHighlight) {
            currentTemporaryHighlight.comment = commentValue;
        }
        saveHighlight(pageNum, viewport, highlightLayer);
        hideHighlightPopup();
    };

    newSaveBtn.addEventListener('click', saveHandler);

    // Allow Ctrl+Enter or Cmd+Enter to save
    commentInput.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            saveHandler();
        }
    });

    newCancelBtn.addEventListener('click', () => {
        cancelHighlight(pageNum, viewport, highlightLayer);
        hideHighlightPopup();
    });

    const clickOutsideHandler = (e) => {
        if (!popup.contains(e.target) && popup.classList.contains('visible')) {
            cancelHighlight(pageNum, viewport, highlightLayer);
            hideHighlightPopup();
            document.removeEventListener('click', clickOutsideHandler);
        }
    };

    // Delay prevents immediate trigger from the mouseup that created the selection
    setTimeout(() => {
        document.addEventListener('click', clickOutsideHandler);
    }, 100);

    const escKeyHandler = (e) => {
        if (e.key === 'Escape' && popup.classList.contains('visible')) {
            cancelHighlight(pageNum, viewport, highlightLayer);
            hideHighlightPopup();
            document.removeEventListener('keydown', escKeyHandler);
        }
    };

    document.addEventListener('keydown', escKeyHandler);
}

function hideHighlightPopup() {
    const popup = document.getElementById('highlight-popup');
    const commentInput = document.getElementById('popup-comment-input');
    const saveBtn = document.getElementById('popup-save-btn');
    popup.classList.remove('visible');
    commentInput.value = '';
    commentInput.classList.remove('error');
    saveBtn.disabled = false;
    saveBtn.classList.remove('disabled');
    currentHighlightData = null;
}

/**
 * Persists the temporary highlight to localStorage and re-renders without the temporary flag,
 * making it a permanent highlight.
 */
function saveHighlight(pageNum, viewport, highlightLayer) {
    if (!currentTemporaryHighlight) {
        return;
    }

    const pageKey = pageNum.toString();
    if (!highlights[pageKey]) {
        highlights[pageKey] = [];
    }
    highlights[pageKey].push(currentTemporaryHighlight);
    saveHighlights();

    currentTemporaryHighlight = null;
    renderHighlights(pageNum, viewport, highlightLayer, false);
    renderComments();
}

/**
 * Discards the temporary highlight and re-renders to remove it from view.
 */
function cancelHighlight(pageNum, viewport, highlightLayer) {
    currentTemporaryHighlight = null;
    renderHighlights(pageNum, viewport, highlightLayer, false);
}

/**
 * Creates a temporary highlight from the current text selection and shows the confirmation popup.
 * Coordinates are converted from viewport space (where selection happens) to PDF space (for storage)
 * because PDF coordinates are scale-independent and will work correctly if the user zooms or the
 * viewport changes.
 */
function addHighlight(pageNum, viewport, textLayer, highlightLayer) {
    const selection = window.getSelection();
    if (selection.rangeCount === 0 || selection.toString().trim() === '') {
        return;
    }

    const selectedText = selection.toString().trim();
    if (selectedText === '') {
        return;
    }

    const selectedSpans = getSelectedTextSpans(selection, highlightLayer);
    if (selectedSpans.length === 0) {
        return;
    }

    // Convert viewport coordinates to PDF coordinates for scale-independent storage
    const rects = selectedSpans.map(spanRect => {
        const topLeftPdf = viewport.convertToPdfPoint(spanRect.left, spanRect.top);
        const bottomRightPdf = viewport.convertToPdfPoint(
            spanRect.left + spanRect.width,
            spanRect.top + spanRect.height
        );

        return {
            x: Math.min(topLeftPdf[0], bottomRightPdf[0]),
            y: Math.max(topLeftPdf[1], bottomRightPdf[1]), // PDF Y-axis is bottom-up
            width: Math.abs(bottomRightPdf[0] - topLeftPdf[0]),
            height: Math.abs(topLeftPdf[1] - bottomRightPdf[1])
        };
    });

    currentTemporaryHighlight = {
        id: generateHighlightId(),
        rects: rects,
        text: selectedText,
        comment: ''
    };

    currentHighlightData = {
        pageNum: pageNum,
        viewport: viewport,
        highlightLayer: highlightLayer
    };

    renderHighlights(pageNum, viewport, highlightLayer, true);
    showHighlightPopup(selectedText, pageNum, viewport, highlightLayer);
    selection.removeAllRanges();
}

/**
 * Renders a single PDF page with three layers: canvas (PDF content), text layer (for selection),
 * and highlight layer (for annotations). The text layer is transparent and positioned over the
 * canvas to enable text selection.
 */
async function renderPage(pageNum, pdfPage, container) {
    // Setup viewport and scale
    const scale = 1.50;
    const viewport = pdfPage.getViewport({ scale: scale });

    // Create DOM structure
    const pageDiv = document.createElement('div');
    pageDiv.className = 'page-container';
    pageDiv.style.width = viewport.width + 'px';
    pageDiv.style.height = viewport.height + 'px';

    // Canvas wrapper positions the three layers (canvas, text, highlights) absolutely
    const canvasWrapper = document.createElement('div');
    canvasWrapper.className = 'canvas-wrapper';
    canvasWrapper.style.width = viewport.width + 'px';
    canvasWrapper.style.height = viewport.height + 'px';

    // Canvas layer: renders the actual PDF content
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    // Text layer: transparent overlay for text selection (positioned above canvas)
    const textLayer = document.createElement('div');
    textLayer.className = 'textLayer';
    textLayer.style.width = viewport.width + 'px';
    textLayer.style.height = viewport.height + 'px';
    textLayer.style.setProperty('--scale-factor', scale);

    // Highlight layer: displays saved and temporary highlights (positioned above text layer)
    const highlightLayer = document.createElement('div');
    highlightLayer.className = 'highlight-layer';

    // Order: canvas (bottom), text (middle), highlights (top)
    canvasWrapper.appendChild(canvas);
    canvasWrapper.appendChild(textLayer);
    canvasWrapper.appendChild(highlightLayer);
    pageDiv.appendChild(canvasWrapper);
    container.appendChild(pageDiv);

    // Render PDF content to canvas
    const renderContext = {
        canvasContext: context,
        viewport: viewport
    };
    await pdfPage.render(renderContext).promise;

    // Render text layer for selection
    // Creates invisible text spans positioned over the canvas that enable native browser text
    // selection. enhanceTextSelection improves accuracy for complex layouts.
    const textContentSource = await pdfPage.getTextContent();
    const textDivs = [];
    const textLayerRenderTask = pdfjsLib.renderTextLayer({
        textContentSource: textContentSource,
        container: textLayer,
        viewport: viewport,
        textDivs: textDivs,
        enhanceTextSelection: true
    });
    await textLayerRenderTask.promise;

    // Render existing highlights from localStorage
    renderHighlights(pageNum, viewport, highlightLayer);

    // Set up text selection listener
    // Small delay ensures selection is fully established before checking, without this, the
    // selection might not be captured correctly.
    textLayer.addEventListener('mouseup', () => {
        setTimeout(() => {
            const selection = window.getSelection();
            if (selection.toString().trim() !== '') {
                addHighlight(pageNum, viewport, textLayer, highlightLayer);
            }
        }, 10);
    });

    return pageDiv;
}

async function render() {
    pdfDocument = await pdfjsLib.getDocument({
        url: documentId,
        cMapUrl: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/',
        cMapPacked: true
    }).promise;

    const viewer = document.getElementById('viewer');
    viewer.innerHTML = '';

    const numPages = pdfDocument.numPages;
    const renderPromises = [];

    for (let pageNum = 1; pageNum <= numPages; pageNum++) {
        const pdfPage = await pdfDocument.getPage(pageNum);
        renderPromises.push(renderPage(pageNum, pdfPage, viewer));
    }

    await Promise.all(renderPromises);
    renderComments();
}

function renderComments() {
    const commentsList = document.getElementById('comments-list');
    commentsList.innerHTML = '';

    // Collect all highlights with comments from all pages
    const allComments = [];
    Object.keys(highlights).forEach(pageKey => {
        const pageHighlights = highlights[pageKey];
        if (Array.isArray(pageHighlights)) {
            pageHighlights.forEach((highlight, index) => {
                // Only show highlights that have comments
                if (highlight && highlight.comment && highlight.comment.trim() !== '') {
                    allComments.push({
                        pageNum: parseInt(pageKey),
                        highlightIndex: index,
                        highlight: highlight
                    });
                }
            });
        }
    });

    // Sort by page number
    allComments.sort((a, b) => a.pageNum - b.pageNum);

    if (allComments.length === 0) {
        return;
    }

    allComments.forEach(({ pageNum, highlightIndex, highlight }) => {
        const commentItem = document.createElement('div');
        commentItem.className = 'comment-item';
        commentItem.setAttribute('data-page', pageNum);
        commentItem.setAttribute('data-index', highlightIndex);

        const highlightText = document.createElement('div');
        highlightText.className = 'comment-highlight';
        highlightText.textContent = highlight.text || 'Selected text';
        commentItem.appendChild(highlightText);

        const commentText = document.createElement('div');
        commentText.className = 'comment-text';
        commentText.textContent = highlight.comment;
        commentItem.appendChild(commentText);

        const commentMeta = document.createElement('div');
        commentMeta.className = 'comment-meta';
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'comment-delete';
        deleteBtn.textContent = 'Delete';
        deleteBtn.addEventListener('click', () => {
            deleteComment(pageNum, highlightIndex);
        });
        commentMeta.appendChild(deleteBtn);

        commentItem.appendChild(commentMeta);
        commentsList.appendChild(commentItem);
    });
}

function deleteComment(pageNum, highlightIndex) {
    const pageKey = pageNum.toString();
    if (highlights[pageKey] && highlights[pageKey][highlightIndex]) {
        highlights[pageKey].splice(highlightIndex, 1);
        if (highlights[pageKey].length === 0) {
            delete highlights[pageKey];
        }
        saveHighlights();
        renderComments();
        
        // Re-render highlights for the affected page
        const pageContainers = document.querySelectorAll('.page-container');
        pageContainers.forEach((container, index) => {
            if (index + 1 === pageNum) {
                const highlightLayer = container.querySelector('.highlight-layer');
                if (highlightLayer && pdfDocument) {
                    pdfDocument.getPage(pageNum).then(page => {
                        const viewport = page.getViewport({ scale: 1.50 });
                        renderHighlights(pageNum, viewport, highlightLayer, false);
                    }).catch(err => {
                        console.warn('Error re-rendering highlights:', err);
                    });
                }
            }
        });
    }
}

render();
