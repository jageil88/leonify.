[app]

title = Leonify
package.name = leonify
package.domain = dev.leon.leonify

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
source.exclude_dirs = tests, bin, .buildozer, .github, __pycache__

version = 1.0.0

# python dependencies
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,ffpyplayer,plyer,sqlite3,certifi

# orientation & presentation
orientation = portrait
fullscreen = 0

# icon & splash (generiert durch generate_assets.py)
icon.filename = icon.png
presplash.filename = presplash.png

# android-spezifisch
android.api = 33
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True

# permissions
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_AUDIO,READ_MEDIA_VIDEO,READ_MEDIA_IMAGES,FOREGROUND_SERVICE,WAKE_LOCK,INTERNET

# verhalten
android.allow_backup = True

# python-for-android branch (stable)
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 0
