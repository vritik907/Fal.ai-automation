import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading, os, sys, requests
import fal_client
import json

# ===================== PATH SAFE =====================
def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = base_dir()
OUTPUT_DIR = os.path.join(BASE_DIR, "images")
CONFIG_FILE = os.path.join(BASE_DIR, "config.txt")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===================== HELPERS =====================
def save_api_key(key):
    with open(CONFIG_FILE, "w") as f:
        f.write(key.strip())

def load_api_key():
    return open(CONFIG_FILE).read().strip() if os.path.exists(CONFIG_FILE) else ""

def fal_image_size(resolution, aspect):
    if aspect == "1:1":
        return "square_hd" if resolution == "1024" else "square"
    if aspect == "16:9":
        return "landscape_16_9"
    if aspect == "9:16":
        return "portrait_16_9"
    if aspect == "4:3":
        return "landscape_4_3"
    if aspect == "3:4":
        return "portrait_4_3"
    return "square"

# ===================== IMAGE UPLOAD =====================
def upload_images(paths):
    urls = []
    for p in paths:
        with open(p, "rb") as f:
            data = f.read()
        # fal_client.upload returns the URL directly as a string
        url = fal_client.upload(data, content_type="image/png")
        urls.append(url)
    return urls

# ===================== GENERATION (FIXED WITH DEBUG) =====================
def generate_one(prompt, idx, app):
    try:
        model = app.model.get().strip()
        args = {"prompt": prompt}

        if "edit" in model:
            if not app.images:
                raise Exception("Edit model requires reference images")
            args["image_urls"] = upload_images(app.images)
        else:
            args["image_size"] = fal_image_size(
                app.resolution.get(),
                app.aspect.get()
            )

        app.log(f"🔍 Calling API with model: {model}")
        
        # Call the API
        result = fal_client.subscribe(model, arguments=args)
        
        # DEBUG: Show what we got back
        app.log(f"📊 Response type: {type(result).__name__}")
        app.log(f"📋 Response keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
        
        # Try to extract URL
        url = None
        
        # Method 1: Standard structure {"images": [{"url": "..."}]}
        if isinstance(result, dict) and "images" in result:
            images = result["images"]
            if isinstance(images, list) and len(images) > 0:
                first = images[0]
                if isinstance(first, dict) and "url" in first:
                    url = first["url"]
                    app.log(f"✓ Found URL in images[0].url")
                elif isinstance(first, str):
                    url = first
                    app.log(f"✓ Found URL as string in images[0]")
        
        # Method 2: Direct {"image": {"url": "..."}}
        if not url and isinstance(result, dict) and "image" in result:
            image = result["image"]
            if isinstance(image, dict) and "url" in image:
                url = image["url"]
                app.log(f"✓ Found URL in image.url")
            elif isinstance(image, str):
                url = image
                app.log(f"✓ Found URL as string in image")
        
        # Method 3: Direct URL
        if not url and isinstance(result, dict) and "url" in result:
            url = result["url"]
            app.log(f"✓ Found direct URL")
        
        if not url:
            # Show full response for debugging
            app.log(f"❌ Could not find URL. Full response:")
            app.log(f"   {json.dumps(result, indent=2)[:500]}")
            raise Exception("Could not find image URL in response")

        # Download and save
        app.log(f"📥 Downloading from: {url[:80]}...")
        img = requests.get(url, timeout=60).content
        out = os.path.join(OUTPUT_DIR, f"image_{idx+1}.png")
        with open(out, "wb") as f:
            f.write(img)

        app.log(f"✅ Saved: {os.path.basename(out)}")
        app.on_done(True)

    except Exception as e:
        import traceback
        app.log(f"❌ Prompt {idx+1} error: {str(e)}")
        app.log(f"   {traceback.format_exc()[:300]}")
        app.on_done(False)

# ===================== THREAD RUNNER =====================
def run_all(prompts, app):
    for i, prompt in enumerate(prompts):
        generate_one(prompt, i, app)

# ===================== GUI APP =====================
class App:
    def __init__(self, root):
        root.title("fal.ai Universal Image Generator")
        root.state("zoomed")

        self.images = []
        self.total = 0
        self.done = 0

        main = ttk.Frame(root, padding=15)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="fal.ai Universal Image Generator",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=10)

        # API KEY
        api = ttk.LabelFrame(main, text="🔑 API Key")
        api.pack(fill="x")
        self.api = ttk.Entry(api, show="*")
        self.api.pack(fill="x", padx=10, pady=5)
        self.api.insert(0, load_api_key())

        # MODEL
        model_frame = ttk.LabelFrame(main, text="🧠 Model")
        model_frame.pack(fill="x", pady=8)
        self.model = ttk.Entry(model_frame)
        self.model.pack(fill="x", padx=10, pady=5)
        self.model.insert(0, "fal-ai/nano-banana-pro/edit")

        # SETTINGS
        settings = ttk.LabelFrame(main, text="⚙️ Settings")
        settings.pack(fill="x", pady=8)

        row = ttk.Frame(settings)
        row.pack(anchor="w", padx=10, pady=5)

        self.aspect = tk.StringVar(value="1:1")
        self.resolution = tk.StringVar(value="1024")

        ttk.Label(row, text="Aspect").pack(side="left")
        ttk.Combobox(row, textvariable=self.aspect,
                     values=["1:1","16:9","9:16","4:3","3:4"],
                     width=7, state="readonly").pack(side="left", padx=5)

        ttk.Label(row, text="Resolution").pack(side="left", padx=10)
        ttk.Combobox(row, textvariable=self.resolution,
                     values=["512","1024"],
                     width=6, state="readonly").pack(side="left")

        # REFERENCE IMAGES
        img_frame = ttk.LabelFrame(main, text="🖼 Reference Images (edit models)")
        img_frame.pack(fill="x", pady=8)

        ttk.Button(img_frame, text="Add Images",
                   command=self.add_images).pack(anchor="w", padx=10)

        self.image_list = ttk.Frame(img_frame)
        self.image_list.pack(fill="x", padx=10, pady=5)

        # PROMPTS
        prompt_frame = ttk.LabelFrame(main, text="📝 Prompts")
        prompt_frame.pack(fill="x", pady=8)

        self.text = tk.Text(prompt_frame, height=6)
        self.text.pack(fill="x", padx=10, pady=5)

        ttk.Button(main, text="Generate Images",
                   command=self.start).pack(pady=10)

        self.progress_label = ttk.Label(main, text="0 / 0")
        self.progress_label.pack(anchor="w")

        self.progress = ttk.Progressbar(main)
        self.progress.pack(fill="x")

        logs = ttk.LabelFrame(main, text="📜 Logs")
        logs.pack(fill="both", expand=True, pady=8)

        self.logs = tk.Listbox(logs)
        self.logs.pack(fill="both", expand=True)

    # ===================== UI HELPERS =====================
    def log(self, msg):
        self.logs.insert(tk.END, msg)
        self.logs.yview(tk.END)
        print(msg)  # Also print to console for debugging

    def add_images(self):
        files = filedialog.askopenfilenames(
            filetypes=[("Images", "*.png *.jpg *.jpeg")]
        )
        for f in files:
            if f not in self.images:
                self.images.append(f)
                row = ttk.Frame(self.image_list)
                row.pack(fill="x", pady=2)
                ttk.Label(row, text=os.path.basename(f)).pack(side="left")
                ttk.Button(row, text="❌",
                           command=lambda p=f, r=row: self.remove_image(p, r))\
                    .pack(side="right")
        self.log(f"🖼 Images selected: {len(self.images)}")

    def remove_image(self, path, row):
        self.images.remove(path)
        row.destroy()

    def start(self):
        key = self.api.get().strip()
        if not key:
            messagebox.showerror("Error", "API key required")
            return

        save_api_key(key)
        os.environ["FAL_KEY"] = key

        prompts = [
            p.strip()
            for p in self.text.get("1.0", tk.END).splitlines()
            if p.strip()
        ]

        if not prompts:
            messagebox.showerror("Error", "No prompts provided")
            return

        self.total = len(prompts)
        self.done = 0

        self.progress["maximum"] = self.total
        self.progress["value"] = 0
        self.progress_label.config(text=f"0 / {self.total}")

        self.log(f"🚀 Model: {self.model.get()}")
        self.log(f"🚀 Generating {self.total} images")

        threading.Thread(
            target=lambda: run_all(prompts, self),
            daemon=True
        ).start()

    def on_done(self, success):
        self.done += 1
        self.progress["value"] = self.done
        self.progress_label.config(text=f"{self.done} / {self.total}")
        if self.done == self.total:
            self.log("🎉 Done!")

# ===================== RUN =====================
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()