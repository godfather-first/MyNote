# MyNote

MyNote is a simple personal task note app built with Python, Kivy, and SQLite.
It stores all data locally in `tasks.db` and does not need registration,
login, cloud sync, a server, or network access.

## Files

- `main.py`: Kivy app entry point and screen registration.
- `database.py`: SQLite schema, migrations, task CRUD, recycle bin, and reminder settings.
- `models.py`: task and deleted-task data models.
- `screens/home_screen.py`: task list, search, filters, swipe delete, completion, and reminders.
- `screens/add_screen.py`: mobile-first new task form.
- `screens/detail_screen.py`: mobile-first task detail, edit, complete, and delete form.
- `screens/recycle_bin_screen.py`: restore deleted tasks retained for ten days.
- `ui_components.py`: reusable mobile-safe inputs, date picker, and priority picker.
- `assets/`: optional bundled app icon, splash image, and CJK font files.
- `requirements.txt`: local Python dependency list.
- `buildozer.spec`: Android APK packaging configuration.

## Run On Desktop

```bash
pip install -r requirements.txt
python main.py
```

## Chinese Font

Kivy's default font may not contain Chinese glyphs, which makes Chinese text
show as square boxes. The app now registers a Chinese-capable font at startup.
On Windows it automatically uses `C:\Windows\Fonts\msyh.ttc`.

For Android APK builds, put one open-source Chinese font into `assets/` using
one of these names:

```text
assets/NotoSansCJKsc-Regular.otf
assets/SourceHanSansSC-Regular.otf
```

The `buildozer.spec` file already includes `ttf`, `ttc`, and `otf` font files.
If no bundled font is present, the app attempts to register common Android
system CJK fonts before falling back to Roboto.

## Build Android APK

The repository includes a GitHub Actions workflow at
`.github/workflows/build-apk.yml`. Push the project to GitHub or run the
workflow manually from the Actions tab, then download the `MyNote-debug-apk`
artifact after the workflow finishes.

The Buildozer project root is `MyNote/`. Local build artifacts, virtual
environments, logs, and desktop `tasks.db` files are excluded from the APK by
`buildozer.spec`.

Install it on an Android phone with:

```bash
adb install *.apk
```

## Database

The app creates `tasks.db` inside Kivy's writable `user_data_dir`, not inside
the APK. The schema stores title, content, status, create/update timestamps,
deadline date, priority, category, and one-shot reminder state. Deleted tasks
move to `deleted_tasks` and are purged after ten days.
