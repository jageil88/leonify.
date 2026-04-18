# Leonify 🎧

offline music player für Android - nimm ein video oder audio file, gib ihm titel & cover, fertig ist dein song.

**features v1:**
- 🎵 lokale video/audio files importieren (mp3, m4a, mp4, mkv, webm, wav, flac, opus, ogg...)
- ✏️ titel, artist und cover selber setzen
- 📚 library mit suche und sortierung
- ❤️ favoriten
- 📝 playlists erstellen, songs hinzufügen, reorderbar
- 🔀 shuffle + 🔁 repeat (off/all/one)
- 🎨 dark theme, lila/pink electric vibe
- 📱 optimiert für Samsung Galaxy A56

**stack:** Python + Kivy + KivyMD + ffpyplayer

---

## 🚀 APK bauen (ohne was auf deinem PC zu installieren)

### 1. GitHub account erstellen
wenn du noch keinen hast: https://github.com/signup

### 2. neues Repository erstellen
- auf github.com → rechts oben **+** → **New repository**
- name: `leonify`
- **public** (damit GitHub Actions gratis läuft)
- **nicht** "initialize with README" anhaken
- **Create repository**

### 3. alle files in das repo hochladen
zwei optionen:

**A) über die webseite (easiest):**
1. auf deinem neuen repo → **"uploading an existing file"** link
2. ziehe **alle files und ordner** aus diesem projekt rein (inkl. `.github` ordner!)
3. commit message: `first commit`
4. **Commit changes**

> ⚠️ wichtig: der versteckte `.github` ordner muss mit! falls github webseite den ordner nicht zeigt → nutze GitHub Desktop oder git CLI.

**B) mit GitHub Desktop (safer für ordner-struktur):**
1. download: https://desktop.github.com/
2. **Clone a repository** → deine neue leonify repo
3. alle files in den geklonten ordner kopieren (inkl. `.github` ordner)
4. GitHub Desktop zeigt alle changes → commit & push

### 4. warten bis die APK gebaut ist
- im repo → **Actions** tab
- du siehst den "Build Leonify APK" workflow laufen 🟡
- dauert ca **10-15 minuten** beim ersten mal (danach durch cache nur ~3-5 min)

### 5. APK herunterladen
- wenn der workflow **grün** ist ✅ → klick drauf
- scroll nach unten zu **Artifacts**
- klick auf **leonify-apk** → lädt eine zip
- entpacken → du hast `leonify-1.0.0-arm64-v8a_armeabi-v7a-debug.apk`

### 6. auf A56 installieren
1. APK per USB / email / cloud (drive/dropbox) aufs handy schieben
2. files-app öffnen → APK antippen
3. android fragt nach **"aus unbekannten quellen installieren erlauben"** → erlauben
4. installieren → app starten 🎉

---

## 🧪 lokal testen (optional)

wenn du Python auf dem PC hast und die app schnell testen willst ohne APK build:

```bash
pip install -r requirements.txt
python main.py
```

ein fenster öffnet sich in phone-proportionen. filechooser funktioniert auch auf Windows/Mac/Linux.

---

## 🛠️ weiterentwicklung

was als nächstes kommen könnte (sag bescheid wenn du eins willst):

- 📥 **YouTube/TikTok URL import** via yt-dlp (brauchen wir für "video-link → song")
- 🎛️ **5-band equalizer** (über Android AudioEffect API)
- 📖 **synced lyrics** (.lrc files)
- 🔔 **notification controls** + lockscreen player
- 🌐 **file manager integration** (share-menü: "mit Leonify öffnen")
- ☁️ **backup/restore** der library

---

## 📂 projekt-struktur

```
leonify/
├── main.py              # app + screens + UI
├── theme.py             # farben (lila/pink)
├── database.py          # SQLite (songs, playlists, favs)
├── player.py            # audio engine (ffpyplayer)
├── importer.py          # file-handling
├── generate_assets.py   # erzeugt icon.png & presplash.png
├── buildozer.spec       # APK build config
├── requirements.txt     # python deps (für lokales testen)
├── .github/
│   └── workflows/
│       └── build.yml    # GitHub Actions CI
├── .gitignore
└── README.md            # diese datei
```

---

## ❓ troubleshooting

**"der build ist rot ❌"**
→ im Actions-tab auf den failed run klicken → build logs angucken → den fehler mir schicken, ich fix's

**"APK installiert aber stürzt ab"**
→ `logcat` vom A56 mit `adb logcat | grep python` → log schicken

**"file-picker findet meine videos nicht"**
→ android permissions checken: app-settings → berechtigungen → dateien & medien erlauben

---

built with 🎧 + Claude
