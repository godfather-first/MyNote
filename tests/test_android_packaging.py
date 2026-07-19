from configparser import ConfigParser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read_buildozer_spec() -> ConfigParser:
    config = ConfigParser()
    config.read(PROJECT_ROOT / "MyNote" / "buildozer.spec", encoding="utf-8")
    return config


def test_buildozer_spec_excludes_local_artifacts_from_apk():
    app = _read_buildozer_spec()["app"]

    include_exts = {item.strip() for item in app["source.include_exts"].split(",")}
    exclude_dirs = {item.strip() for item in app["source.exclude_dirs"].split(",")}
    exclude_exts = {item.strip() for item in app["source.exclude_exts"].split(",")}
    exclude_patterns = {item.strip() for item in app["source.exclude_patterns"].split(",")}

    assert "db" not in include_exts
    assert {"py", "ttf", "ttc", "otf"}.issubset(include_exts)
    assert {".venv", "venv", "bin", "__pycache__", ".buildozer"}.issubset(exclude_dirs)
    assert {"db", "sqlite", "sqlite3", "log", "zip"}.issubset(exclude_exts)
    assert "tasks.db" in exclude_patterns


def test_buildozer_spec_targets_modern_android_without_network_permissions():
    app = _read_buildozer_spec()["app"]
    archs = {item.strip() for item in app["android.archs"].split(",")}
    requirements = {item.strip() for item in app["requirements"].split(",")}

    assert requirements == {"python3", "kivy"}
    assert int(app["android.minapi"]) >= 24
    assert {"arm64-v8a", "armeabi-v7a"}.issubset(archs)
    assert app["orientation"] == "portrait"
    assert app["android.permissions"].strip() == ""


def test_github_apk_workflow_runs_tests_before_buildozer():
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "build-apk.yml").read_text(
        encoding="utf-8"
    )

    test_index = workflow.index("Run tests before packaging")
    build_index = workflow.index("Build debug APK")

    assert test_index < build_index
    assert "xvfb-run -a python -m pytest -q" in workflow
    assert "xvfb" in workflow
    assert "buildozer -v android debug" in workflow
