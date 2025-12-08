// Shared PDF viewer for rendering resumes with highlights.
// Kept inside an IIFE so only the public factory leaks to window;
// everything else stays private in the closure.
//
// Usage:
//   const viewer = createResumeViewer({
//     pdfUrl: string,
//     scale: number,
//     containerId: "viewer",
//     renderHighlightsForPage: (pageNum, viewport, highlightLayer) => {},
//     onTextSelection: (pageNum, viewport, textLayer, highlightLayer) => {} // optional
//   });
//   await viewer.render();
//   const pdfDoc = viewer.getDocument();
(function () {
  function createResumeViewer({
    pdfUrl,
    scale = 1.5,
    containerId = "viewer",
    renderHighlightsForPage,
    onTextSelection,
  }) {
    let pdfDocument = null;

    async function renderPage(pageNum, pdfPage, container) {
      const viewport = pdfPage.getViewport({ scale });

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
      textLayer.style.setProperty("--scale-factor", scale);

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

      // Render text layer only when selection is needed
      if (onTextSelection) {
        const textContent = await pdfPage.getTextContent();
        await pdfjsLib.renderTextLayer({
          textContent,
          container: textLayer,
          viewport,
          textDivs: [],
          enhanceTextSelection: true,
        }).promise;
      }

      // initial highlight render
      if (renderHighlightsForPage) {
        renderHighlightsForPage(pageNum, viewport, highlightLayer);
      }

      // hook selection for interactive mode
      if (onTextSelection) {
        textLayer.addEventListener("mouseup", () => {
          setTimeout(() => {
            onTextSelection(pageNum, viewport, textLayer, highlightLayer);
          }, 10);
        });
      }

      return pageDiv;
    }

    async function renderAll() {
      pdfDocument = await pdfjsLib.getDocument({
        url: pdfUrl,
        cMapUrl:
          "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/",
        cMapPacked: true,
      }).promise;

      const viewer = document.getElementById(containerId);
      viewer.innerHTML = "";

      const numPages = pdfDocument.numPages;
      for (let pageNum = 1; pageNum <= numPages; pageNum++) {
        const pdfPage = await pdfDocument.getPage(pageNum);
        await renderPage(pageNum, pdfPage, viewer);
      }
    }

    return {
      render: renderAll,
      getDocument: () => pdfDocument,
    };
  }

  window.createResumeViewer = createResumeViewer;
})();
