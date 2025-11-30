# 🎯 CUSTOMIZATION CHECKLIST

## 📝 What You Need to Update

### 1. Developer Information (REQUIRED)

**File**: `templates/developers.html`

**What to change:**

#### Developer 1 (Line 14-30):
```html
<!-- CHANGE THESE -->
<h2 class="developer-name">Developer Name 1</h2>
<p class="developer-title">Lead ML Engineer & Security Researcher</p>
<p class="developer-description">
    Specializes in machine learning algorithms for cybersecurity applications. 
    Focused on developing advanced classification models for threat detection and analysis.
    Expert in Python, Deep Learning, and Threat Intelligence.
</p>
<a href="https://linkedin.com/in/your-profile" target="_blank" class="social-link">
```

**Replace with:**
- Your actual name
- Your role/title
- Your description (3-4 lines)
- Your LinkedIn URL: `https://linkedin.com/in/YOUR-USERNAME`

#### Developer 2 (Line 35-51):
```html
<!-- CHANGE THESE -->
<h2 class="developer-name">Developer Name 2</h2>
<p class="developer-title">Full Stack Developer & Data Scientist</p>
<p class="developer-description">
    Experienced in building secure web applications and data analysis pipelines.
    Passionate about cybersecurity and creating intuitive interfaces for complex systems.
    Proficient in Flask, React, and Data Visualization.
</p>
<a href="https://linkedin.com/in/your-profile" target="_blank" class="social-link">
```

**Replace with:**
- Second developer's name
- Their role/title
- Their description
- Their LinkedIn URL

---

### 2. Optional Customizations

#### Change Theme Colors
**File**: `static/css/style.css` (Lines 5-15)

```css
:root {
    --primary-color: #00ff41;      /* Change to your preferred accent color */
    --secondary-color: #0d0d0d;    /* Background color */
    --accent-color: #1a1a1a;       /* Card backgrounds */
}
```

**Popular alternatives:**
- Cyber Blue: `#00d4ff`
- Hacker Red: `#ff0055`
- Purple Tech: `#a855f7`
- Keep Matrix Green: `#00ff41` (current)

#### Change Server Port
**File**: `app.py` (Line 303)

```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change 5000 to your port
```

#### Add Developer Photos
Replace emoji avatars (👨‍💻) with actual images:

**File**: `templates/developers.html` (Lines 13, 36)

Replace:
```html
<div class="developer-avatar">
    👨‍💻
</div>
```

With:
```html
<div class="developer-avatar">
    <img src="{{ url_for('static', filename='images/dev1.jpg') }}" 
         alt="Developer 1" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">
</div>
```

Then add images to: `static/images/dev1.jpg` and `static/images/dev2.jpg`

---

## ✅ Quick Start Commands

### 1. Update Developer Info
```bash
nano templates/developers.html
# or
code templates/developers.html
```

### 2. Start the Server
```bash
cd /home/ibrahim-sayys/Projects/ThreatLens/_Web_interface_for_fyp
./run.sh
```

### 3. Test in Browser
Open: http://localhost:5000

### 4. Test Each Feature
- ✓ Home page loads
- ✓ Classify single URL (try: https://github.com)
- ✓ Classify batch URLs (use sample_urls.csv)
- ✓ Orion Intelligence link works
- ✓ Developers page shows your info
- ✓ About page loads

---

## 🔍 Where to Find What

| Feature | File | Lines |
|---------|------|-------|
| Developer Names | `templates/developers.html` | 14, 37 |
| LinkedIn URLs | `templates/developers.html` | 23, 46 |
| Descriptions | `templates/developers.html` | 16-20, 39-43 |
| Colors | `static/css/style.css` | 5-15 |
| Port | `app.py` | 303 |
| Navigation | `templates/base.html` | 12-20 |

---

## 🚀 Ready to Launch?

### Pre-Launch Checklist:
- [ ] Updated Developer 1 name and LinkedIn
- [ ] Updated Developer 2 name and LinkedIn  
- [ ] Updated developer descriptions
- [ ] Tested single URL classification
- [ ] Tested batch processing
- [ ] Checked all navigation links
- [ ] Verified models load correctly

### Launch Command:
```bash
./run.sh
```

### Access URL:
```
http://localhost:5000
```

---

## 📸 Pages Overview

1. **Home (/)** - Landing page with feature cards
2. **Classify (/classify)** - Single & batch URL analysis
3. **Orion (/orion)** - Redirects to external platform
4. **Developers (/developers)** - YOUR INFO HERE ⭐
5. **About (/about)** - System information

---

## 💡 Pro Tips

1. **Test Before Deploy**: Always test locally first
2. **Use XGBoost**: Best accuracy for classification
3. **Batch Limit**: Max 50 URLs per batch
4. **CSV Format**: Must have "url" column
5. **Tor Setup**: Only needed for .onion sites

---

## 🎨 Theme Preview

**Current Theme:**
- Background: Dark (matrix-style)
- Accent: Neon Green (#00ff41)
- Font: Courier New (monospace)
- Style: Minimalistic cybersecurity

**Looks like:**
- Matrix movie aesthetic
- Terminal/command-line inspired
- Clean and professional
- Easy to read

---

## ❓ Need Help?

**Read the docs:**
- `QUICKSTART.md` - Quick guide
- `README_INTERFACE.md` - Full documentation  
- `SUMMARY.md` - Implementation details

**Common Issues:**
- Port in use: `lsof -ti:5000 | xargs kill -9`
- Models not loading: Check `_Website_classificatio_v1/` folder
- Dependencies missing: `pip install -r requirements.txt`

---

## ✨ You're All Set!

**Just update the developer info and you're ready to go! 🚀**

Start with:
```bash
nano templates/developers.html
```

Then:
```bash
./run.sh
```

**Good luck with your project! 🔒**

