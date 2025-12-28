import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading, asyncio, os, sys, base64, requests
import fal_client

# ===================== PATH SAFE =====================
def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = base_dir()
OUTPUT_DIR = os.path.join(BASE_DIR, "images")
CONFIG_FILE = os.path.join(BASE_DIR, "config.txt")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MODEL = "fal-ai/flux/schnell"

# ===================== HELPERS =====================
def save_api_key(key):
    with open(CONFIG_FILE, "w") as f:
        f.write(key.strip())

def load_api_key():
    return open(CONFIG_FILE).read().strip() if os.path.exists(CONFIG_FILE) else ""

def encode_images(paths):
    return [base64.b64encode(open(p, "rb").read()).decode() for p in paths]

def image_size(res, ratio):
    r = {"1:1": (1,1), "16:9": (16,9), "9:16": (9,16), "4:3": (4,3), "3:4": (3,4)}
    w = int(res)
    rw, rh = r[ratio]
    return f"{w}x{int(w * rh / rw)}"

# ===================== ASYNC =====================
async def generate_one(prompt, idx, app):
    try:
        args = {
            "prompt": prompt,
            "image_size": image_size(app.resolution.get(), app.aspect.get())
        }
        if app.images:
            args["image_base64"] = encode_images(app.images)

        result = await fal_client.run_async(MODEL, arguments=args)
        if "images" not in result:
            raise Exception("No images returned (billing / API issue)")

        url = result["images"][0]["url"]
        img = requests.get(url, timeout=30).content
        with open(os.path.join(OUTPUT_DIR, f"image_{idx+1}.png"), "wb") as f:
            f.write(img)

        app.on_done()
    except Exception as e:
        app.log(f"❌ Prompt {idx+1}: {e}")
        app.on_done()

async def run_all(prompts, app):
    await asyncio.gather(*[generate_one(p, i, app) for i, p in enumerate(prompts)])

# ===================== APP =====================
class App:
    def __init__(self, root):
        root.title("fal.ai Bulk Image Generator")
        root.state("zoomed")

        self.images = []
        self.prompts = []
        self.total = 0
        self.done = 0

        # -------- CANVAS LAYOUT (FIXED) --------
        canvas = tk.Canvas(root, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        self.main = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=self.main, anchor="nw")

        def resize(event):
            canvas.itemconfig(window, width=event.width)

        canvas.bind("<Configure>", resize)
        self.main.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        self.main.columnconfigure(0, weight=1)

        # -------- UI --------
        def section(title):
            f = ttk.LabelFrame(self.main, text=title, padding=12)
            f.pack(fill="x", padx=20, pady=8)
            return f

        ttk.Label(self.main, text="fal.ai Bulk Image Generator",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=20, pady=10)

        api = section("🔑 API Key")
        self.api = ttk.Entry(api, show="*")
        self.api.pack(fill="x")
        self.api.insert(0, load_api_key())

        settings = section("⚙️ Settings")
        row = ttk.Frame(settings)
        row.pack(anchor="w")
        self.aspect = tk.StringVar(value="1:1")
        self.resolution = tk.StringVar(value="1024")
        ttk.Label(row, text="Aspect Ratio").pack(side="left")
        ttk.Combobox(row, textvariable=self.aspect,
                     values=["1:1","16:9","9:16","4:3","3:4"],
                     width=6, state="readonly").pack(side="left", padx=5)
        ttk.Label(row, text="Resolution").pack(side="left", padx=10)
        ttk.Combobox(row, textvariable=self.resolution,
                     values=["512","1024","2048"],
                     width=6, state="readonly").pack(side="left")

        images = section("🖼 Reference Images (used for all prompts)")
        ttk.Button(images, text="Add Images", command=self.add_images).pack(anchor="w")
        self.image_list = ttk.Frame(images)
        self.image_list.pack(fill="x", pady=5)

        prompts = section("📝 Paste Prompts (one per line)")
        self.text = tk.Text(prompts, height=6)
        self.text.pack(fill="x")

        ttk.Button(self.main, text="Generate Images", command=self.start)\
            .pack(pady=10)

        self.progress_label = ttk.Label(self.main, text="0 / 0")
        self.progress_label.pack(anchor="w", padx=20)

        self.progress = ttk.Progressbar(self.main)
        self.progress.pack(fill="x", padx=20)

        logs = section("📜 Logs")
        self.logs = tk.Listbox(logs, height=8)
        self.logs.pack(side="left", fill="both", expand=True)
        ttk.Scrollbar(logs, command=self.logs.yview)\
            .pack(side="right", fill="y")
        self.logs.config(yscrollcommand=lambda *a: None)

    # -------- LOGIC --------
    def log(self, msg):
        self.logs.insert(tk.END, msg)
        self.logs.yview(tk.END)

    def add_images(self):
        files = filedialog.askopenfilenames(filetypes=[("Images","*.png *.jpg *.jpeg")])
        for f in files:
            if f not in self.images:
                self.images.append(f)
                row = ttk.Frame(self.image_list)
                row.pack(fill="x", pady=2)
                ttk.Label(row, text=os.path.basename(f)).pack(side="left")
                ttk.Button(row, text="❌",
                           command=lambda p=f, r=row: self.remove_image(p, r))\
                    .pack(side="right")
        self.log(f"🖼 Images: {len(self.images)}")

    def remove_image(self, path, row):
        if path in self.images:
            self.images.remove(path)
            row.destroy()
            self.log(f"🗑 Removed {os.path.basename(path)}")

    def start(self):
        key = self.api.get().strip()
        if not key:
            messagebox.showerror("Error", "API key required")
            return

        save_api_key(key)
        os.environ["FAL_KEY"] = key

        self.prompts = [p.strip() for p in self.text.get("1.0", tk.END).splitlines() if p.strip()]
        if not self.prompts:
            messagebox.showerror("Error", "No prompts provided")
            return

        self.total = len(self.prompts)
        self.done = 0
        self.progress["maximum"] = self.total
        self.progress["value"] = 0
        self.progress_label.config(text=f"0 / {self.total}")

        self.log(f"🚀 Generating {self.total} images")

        threading.Thread(
            target=lambda: asyncio.run(run_all(self.prompts, self)),
            daemon=True
        ).start()

    def on_done(self):
        self.main.after(0, self.update)

    def update(self):
        self.done += 1
        self.progress["value"] = self.done
        self.progress_label.config(text=f"{self.done} / {self.total}")
        if self.done == self.total:
            self.log("🎉 Done")

# ===================== RUN =====================
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
