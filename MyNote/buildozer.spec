[app]
title = MyNote
package.name = mynote
package.domain = org.local
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,ttf,ttc,otf
version = 0.1.0
requirements = python3,kivy,sqlite3
orientation = portrait
fullscreen = 0
android.minapi = 24
android.api = 35
android.build_tools_version = 35.0.0
android.archs = arm64-v8a
android.permissions =
android.accept_sdk_license = True

# (Optional) Place a font file in assets/ to bundle CJK font support:
# source.include_exts already includes ttf,ttc,otf

# (Optional) Splash screen and app icon (place PNG in assets/):
# presplash.filename = %(source.dir)s/assets/presplash.png
# icon.filename = %(source.dir)s/assets/icon.png

# Logging on Android — use 'adb logcat -s python' to see app logs
android.log_handler = logcat

# Release build signing (generate keystore first, then uncomment):
# android.release_artifact = apk
# android.keyalias = mynote-key
# android.keystore = ./mynote-release-key.keystore
# android.storepass = <your-keystore-password>
# android.keypass = <your-key-password>

[buildozer]
log_level = 2
warn_on_root = 1
