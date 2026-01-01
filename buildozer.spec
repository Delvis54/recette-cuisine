[app]
title = Recettes Africaines
package.name = recettes
package.domain = org.example
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg
version = 0.1
requirements = python3,kivy,requests,pillow
# (debug build) will be unsigned and good for sideloading
android.arch = armeabi-v7a
orientation = portrait
fullscreen = 0

# (optional) add permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE

# (logging)
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
