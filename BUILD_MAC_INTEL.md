# 🛠 Build and Install `app.py` on macOS Intel

This guide explains how to:

1. Install and test the `app.py` locally  
2. Convert it into a **macOS Intel application (`.app`)**

This documentation is tailored for Intel-based Macs (x86_64).

---

## ✅ Part 1 — Install and Run `app.py`

### 📋 Step 1: Clone the Repository

If you haven’t already:

```bash
git clone https://github.com/vritik907/Fal.ai-automation.git
cd Fal.ai-automation
```

---

### 🐍 Step 2: Install Python (if not installed)

Check your Python version:

```bash
python3 --version
```

If Python 3.10+ is not installed:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.11
```

Verify:

```bash
python3 --version
```

---

### 🧪 Step 3: Create & Activate a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 📥 Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install fal-client requests
```

> If the repo includes `requirements.txt`, you can alternatively run:
>
> ```bash
> pip install -r requirements.txt
> ```

---

### ⚙️ Step 5: Configure API Key

Open `app.py` and add your fal.ai API key where prompted or set it as an environment variable:

```bash
export FAL_KEY="your_api_key_here"
```

---

### ▶️ Step 6: Run the App

```bash
python app.py
```

Make sure the app opens and runs correctly before packaging.

---

## ✅ Part 2 — Build Intel macOS Application (.app)

After confirming that `app.py` runs locally, follow these steps.

---

## 🏗 Step 1: Install PyInstaller

```bash
pip install pyinstaller
```

---

## 🏗 Step 2: Build the App

Run:

```bash
pyinstaller \
  --name "fal.ai Image Generator" \
  --windowed \
  --onedir \
  app.py
```

This will generate:

```
dist/
└── fal.ai Image Generator.app
```

---

## 🚀 Step 3: Test the Built App

Open it from Finder:

```
dist/fal.ai Image Generator.app
```

### ➤ First Launch Security

If macOS shows a warning:

➡️ Right-click (or Control-click) → **Open**  
➡️ Click **Open** again

This allows the unsigned app to run.

---

## 🔐 (Optional) Fix Gatekeeper

If needed:

```bash
xattr -rd com.apple.quarantine "/Applications/fal.ai Image Generator.app"
```

---

## 📌 Notes & Troubleshooting

### ❓ App crashes immediately
Run the executable from terminal to see logs:

```bash
./dist/fal.ai\\ Image\\ Generator.app/Contents/MacOS/fal.ai\\ Image\\ Generator
```

---

### ❓ Python modules missing
Make sure your virtual environment is activated when running PyInstaller.

---

## 🧠 Summary

You’ve now:

1. Installed `app.py` locally
2. Verified it runs
3. Built a native macOS Intel application

Enjoy your **standalone macOS build!**

---

## 📦 Optional Next Steps

You can also:

- Create a **DMG installer**
- Add an application **icon**
- Sign/Notarize the app with Apple
- Build **Universal (Intel + ARM)** app

If you want help with those, just ask! 🚀
