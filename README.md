# Convince Me That — PDF Generator

A web app that generates print-ready 6-page student argument packets from four inputs.

## Running Locally

**Step 1 — Install dependencies**
```
pip3 install flask reportlab gunicorn
```

**Step 2 — Run the app**
```
cd cmt_app
python3 app.py
```

**Step 3 — Open in browser**
```
http://localhost:5000
```

Fill in the form, click Generate, and your PDF downloads immediately.

---

## Deploying to Render (free hosting)

1. Push this folder to a GitHub repository
2. Go to https://render.com and sign up (free)
3. Click **New → Web Service**
4. Connect your GitHub repo
5. Render will auto-detect the Procfile — just click **Deploy**
6. Your app gets a live URL like `https://cmt-generator.onrender.com`

That's it. No server management, no cost for low traffic.

---

## Project Structure

```
cmt_app/
  app.py            ← Flask backend + PDF generation
  requirements.txt  ← Dependencies
  Procfile          ← Tells Render how to run the app
  templates/
    index.html      ← The web interface
```

## Customizing

The PDF logic lives entirely inside the `build_pdf()` function in `app.py`.
The four CONFIG variables from `cmt_v4.py` are now the four form fields:
- `PROMPT`     → "The Convince Me That statement" textarea
- `TEXT_TITLE` → "Text or unit title" input
- `GRADE`      → Grade level dropdown
- `DOMAIN`     → Subject domain pill selector
