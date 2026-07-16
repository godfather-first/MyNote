[app]
title = MyNote
package.name = mynote
package.domain = org.local
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 0.1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.minapi = 23
android.api = 35
android.build_tools_version = 35.0.0
android.archs = arm64-v8a, armeabi-v7a
android.permissions =
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
