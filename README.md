# Background Remover Web App

This project is a simple Flask-based web app I built to remove backgrounds from images using the **rembg** library. It’s lightweight, easy to run, and has a clean, responsive interface that works smoothly on both mobile and desktop screens.

The whole point of this project was to create something practical that develops ability to put together a full end-to-end app using Python, Flask, HTML/CSS/JS, and a bit of UI thinking.

---

## 🔧 What This App Does

* Lets you upload an image (PNG/JPG/JPEG)
* Removes the background using **rembg** and **Pillow (PIL)**
* Shows you a preview of the output right in the browser
* Lets you download the processed image with one click
* Everything happens in your browser session—no external storage

---
### 🔧 How This Application Works (Technical Overview)

This project combines **Flask**, **rembg**, and **Pillow (PIL)** to create a simple background-removal web application. 
<br>Flask acts as the web framework responsible for routing, request handling, validation, and returning JSON or rendered templates.
<br> When a user uploads an image, Flask first verifies the file’s extension and size, then reads the raw bytes. These bytes are passed through **Pillow**, which performs a lightweight integrity check to ensure the file is a real image before any processing occurs.
<br> Once validated, the bytes are fed into **rembg**, a powerful machine-learning-based background removal engine that outputs a clean PNG with a transparent alpha channel.
<br> The processed image is then written to the `static/outputs` directory using a secure, UUID-based filename to avoid collisions. Flask then exposes three key endpoints: one to **view** the processed transparent PNG in the browser, one to **download** it as an attachment, and one to **serve** the raw bytes directly (useful for UI previews).
<br> Every function in the backend is documented, error-handled, and validation-checked, ensuring that corrupted files, oversized uploads, or processing failures never crash the app. Together, these libraries form a smooth pipeline: Flask handles the delivery, Pillow protects the input, rembg performs the heavy lifting, and the frontend consumes the output seamlessly.

---

## 🗂 Project Structure

```
project_root/
│
├── app.py
├── requirements.txt
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
└── templates/
    └── index.html
```

---

## ▶️ How to Run the App

Make sure your virtual environment is created and activated.

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the server:

```bash
python app.py
```

3. Open your browser and visit:

```
http://127.0.0.1:5000/
```

---

## 💡 Why I Built This

I wanted a hands-on project where I could:

* Work with image processing
* Use Flask in a proper structured way
* Build a UI that feels smooth and intuitive
* Produce something that’s easy to maintain and extend



---

## 🧩 Key Libraries Used

* **Flask** — Server + routing
* **rembg** — Actual background removal
* **Pillow** — Image handling

---

## 📝 Notes

* The app doesn’t save any images permanently. Everything stays in memory.
* The UI is intentionally simple so users can upload, preview, and download in a few seconds.
* All code is fully commented to help future me (or anyone else) understand what’s going on.

---

## 📌 Future Improvements (Optional)

* Drag-and-drop uploader
* A processing spinner animation
* Option to adjust output size or file type
* Toggle between preview modes

---


