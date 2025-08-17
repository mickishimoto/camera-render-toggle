# 🎥 Camera Render Tools (Blender Add-on)

**Author: C-gy**  
A Blender add-on for managing multiple cameras with ease. Includes two tools:

---

## ✨ Features

### 1. Camera Render Toggle

- Disables rendering for all cameras except the active one.
- Press again to re-enable all cameras.
- Automatically updates visibility of collections to ensure proper exclusion.

### 2. Batch Render Cameras

- Renders animation only for cameras that are currently enabled for rendering.
- Respects your current render engine and output format.
- You can select an output directory from the UI.
- Option to shut down the system after rendering.
- Each render is saved as a separate video file with camera name and timestamp.
- A log file (`render_log.txt`) is generated with time stamps and durations.

---

## 📂 Location in Blender

`3D Viewport` → `N Panel` → `C-gy` tab

---

## 🛠 Installation

1. Download this repository as a `.zip` file  
2. In Blender:  
   `Edit > Preferences > Add-ons > Install...`  
3. Select the `.zip` file and enable the add-on  
4. Use tools from the `C-gy` tab in the 3D Viewport sidebar

---

## 🧪 Requirements

- Blender 4.0 or newer  
- Works with Cycles, Eevee, and other engines  
- OS shutdown requires appropriate permissions

---

## 📜 License

This add-on is free and open-source.  
Feel free to use and modify it as needed.

---

## 🤝 Feedback & Contributions

Suggestions, improvements, or feature requests are always welcome.  
Feel free to open an issue or fork the repository.

---

