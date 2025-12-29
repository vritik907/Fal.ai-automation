# 🛠 Build macOS Intel Application from `app.py` (Local)

This guide explains how to convert **`app.py`** into a **macOS Intel `.app` application** on your own machine.

---

## ✅ Requirements

### Hardware
- **Intel-based Mac** (x86_64)

### Software
- **macOS 11 (Big Sur) or newer**
- **Python 3.10+** (recommended: 3.11)
- **Internet connection**

---

## 🔎 Verify Intel Mac

Open Terminal and run:

```bash
uname -m
```

Expected output:

```
x86_64
```

---

## 🐍 Install Python (if not installed)

### Option 1 – Homebrew (recommended)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.11
```

Verify:
```bash
python3 --version
```

---

## 📁 Project Structure

```
project/
├── app.py
├── requirements.txt   (optional)
└── assets/            (optional)
```

---

## 📦 Create Virtual Environment (Recommended)

```bash
cd project
python3 -m venv venv
source venv/bin/activate
```

---

## 📥 Install Dependencies

```bash
pip install --upgrade pip
pip install fal-client requests pyinstaller
```

---

## 🧪 Test App Before Building

```bash
python app.py
```

---

## 🏗 Build Intel macOS App

```bash
pyinstaller \
  --name "fal.ai Image Generator" \
  --windowed \
  --onedir \
  app.py
```

---

## 📂 Output Location

```
dist/
└── fal.ai Image Generator.app
```

---

## 🚀 Run the App

Right-click → Open (first launch).

---

## 🔐 Gatekeeper Fix (if needed)

```bash
xattr -rd com.apple.quarantine "/Applications/fal.ai Image Generator.app"
```

---

## ❌ Common Errors

### App closes immediately
Run from terminal:
```bash
./dist/fal.ai\ Image\ Generator.app/Contents/MacOS/fal.ai\ Image\ Generator
```

---

## ✅ Summary

✔ Intel-native macOS app  
✔ No Python needed for end users  
✔ One-time security approval  

---

Happy building 🚀
