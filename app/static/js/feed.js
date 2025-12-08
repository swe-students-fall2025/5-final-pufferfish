let currentIndex = 0;

async function generateThumbnail(pdfUrl, canvas) {
    try {
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

        const loadingTask = pdfjsLib.getDocument(pdfUrl);
        const pdf = await loadingTask.promise;
        const page = await pdf.getPage(1);

        const scale = 1.5;
        const viewport = page.getViewport({ scale });

        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        await page.render({
            canvasContext: context,
            viewport: viewport
        }).promise;
    } catch (error) {
        console.error('Error generating thumbnail:', error);
    }
}

function updateResume(index) {
    if (!window.feedResumes || window.feedResumes.length === 0) return;

    const resume = window.feedResumes[index];
    const canvas = document.getElementById('resume-thumbnail');
    const detailsDisplay = document.getElementById('details-display');

    if (canvas && resume._id) {
        const pdfUrl = `/resume/${resume._id}/pdf`;
        generateThumbnail(pdfUrl, canvas);
    }

    if (detailsDisplay) {
        detailsDisplay.innerHTML = `
            <p><strong>Title:</strong> ${resume.title || 'N/A'}</p>
            <p><strong>Summary:</strong> ${resume.summary || 'N/A'}</p>
            <p><strong>Skills:</strong> ${resume.skills || 'N/A'}</p>
            <p><strong>Experience:</strong> ${resume.experience_level || 'N/A'}</p>
            <p><strong>Location:</strong> ${resume.location || 'N/A'}</p>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    if (window.feedResumes && window.feedResumes.length > 0) {
        updateResume(0);
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentIndex > 0) {
                currentIndex--;
                updateResume(currentIndex);
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentIndex < window.feedResumes.length - 1) {
                currentIndex++;
                updateResume(currentIndex);
            }
        });
    }
});