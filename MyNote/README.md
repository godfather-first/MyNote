# MyNote

MyNote is a simple personal task note app built with Python, Kivy, and SQLite.
It stores all data locally in `tasks.db` and does not need registration,
login, cloud sync, a server, or network access.

## Files

- `main.py`: Kivy app entry point and screen registration.
- `database.py`: SQLite table creation and task CRUD operations.
- `models.py`: `Task` data model.
- `screens/home_screen.py`: home task list, status toggle, and long-press delete.
- `screens/add_screen.py`: new task form.
- `screens/detail_screen.py`: task detail, edit, complete, and delete form.
- `assets/`: reserved for icons and images.
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

## Build Android APK

Buildozer is best run on Linux or WSL. From the `MyNote` directory:

```bash
pip install buildozer
buildozer android debug
```

After the build finishes, the APK is generated under:

```text
bin/
```

Install it on an Android phone with:

```bash
adb install bin/*.apk
```

## Database

The app automatically creates `tasks.db` with the `tasks` table. The table
contains `id`, `title`, `content`, `status`, `create_time`, `update_time`,
and `due_date`. The `due_date` column supports the required optional deadline
field while keeping everything local.
