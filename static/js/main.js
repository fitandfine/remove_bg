const fileInput = document.getElementById("imageInput");
const previewImg = document.getElementById("previewImg");
const processBtn = document.getElementById("processBtn");
const loader = document.getElementById("loader");

const cameraBtn = document.getElementById("cameraBtn");
const cameraStream = document.getElementById("cameraStream");
const captureBtn = document.getElementById("captureBtn");
const cameraCanvas = document.getElementById("cameraCanvas");

const resultBox = document.getElementById("resultBox");
const resultImg = document.getElementById("resultImg");
const viewLink = document.getElementById("viewLink");
const downloadLink = document.getElementById("downloadLink");

let cameraActive = false;
let capturedBlob = null;

/* ----------------------------------------------------------
   FILE PICKER PREVIEW
---------------------------------------------------------- */
fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (!file) return;

    previewImg.src = URL.createObjectURL(file);
    previewImg.classList.remove("hidden");
    capturedBlob = null; // Clear camera image
    processBtn.classList.remove("hidden");
});

/* ----------------------------------------------------------
   CAMERA HANDLING
---------------------------------------------------------- */

cameraBtn.addEventListener("click", async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });

        cameraStream.srcObject = stream;

        cameraStream.classList.remove("hidden");
        captureBtn.classList.remove("hidden");

        fileInput.value = ""; // Clear file input
        capturedBlob = null;
    } catch (err) {
        alert("Camera not available or permission denied.");
    }
});

captureBtn.addEventListener("click", () => {
    const ctx = cameraCanvas.getContext("2d");
    cameraCanvas.width = cameraStream.videoWidth;
    cameraCanvas.height = cameraStream.videoHeight;

    ctx.drawImage(cameraStream, 0, 0);

    cameraStream.srcObject.getTracks().forEach(track => track.stop());

    cameraStream.classList.add("hidden");
    captureBtn.classList.add("hidden");

    cameraCanvas.toBlob(blob => {
        capturedBlob = blob;

        previewImg.src = URL.createObjectURL(blob);
        previewImg.classList.remove("hidden");

        processBtn.classList.remove("hidden");
    }, "image/png");
});

/* ----------------------------------------------------------
   SEND TO SERVER /remove
---------------------------------------------------------- */
processBtn.addEventListener("click", () => {
    loader.classList.remove("hidden");

    let formData = new FormData();

    if (capturedBlob) {
        formData.append("image", capturedBlob, "camera.png");
    } else {
        let file = fileInput.files[0];
        if (!file) {
            alert("Select or capture an image first.");
            return;
        }
        formData.append("image", file);
    }

    fetch("/remove", {
        method: "POST",
        body: formData
    })
        .then(res => res.json())
        .then(data => {
            loader.classList.add("hidden");

            if (!data.success) {
                alert(data.error);
                return;
            }

            resultBox.classList.remove("hidden");
            resultImg.src = "/static/outputs/" + data.filename;

            viewLink.href = data.view_url;
            downloadLink.href = data.download_url;
        })
        .catch(err => {
            loader.classList.add("hidden");
            alert("Error processing image.");
        });
});
