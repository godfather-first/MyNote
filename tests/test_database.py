from datetime import datetime, timedelta

from database import RECYCLE_BIN_RETENTION_DAYS, TaskDatabase


def test_delete_moves_task_to_recycle_bin_and_restore_returns_it(tmp_path):
    db = TaskDatabase(db_dir=str(tmp_path))
    task_id = db.add_task(
        title="准备周报",
        content="汇总关键事项",
        due_date="2026-07-19",
        priority=1,
        category="工作",
    )

    db.delete_task(task_id)

    assert db.get_task(task_id) is None
    deleted = db.get_deleted_tasks()
    assert len(deleted) == 1
    assert deleted[0].title == "准备周报"
    assert deleted[0].category == "工作"

    restored_id = db.restore_deleted_task(deleted[0].id)
    restored = db.get_task(restored_id)
    assert restored is not None
    assert restored.title == "准备周报"
    assert restored.category == "工作"
    assert db.get_deleted_tasks() == []
    db.close()


def test_purge_expired_deleted_tasks_keeps_only_recent_items(tmp_path):
    db = TaskDatabase(db_dir=str(tmp_path))
    old_time = datetime.now() - timedelta(days=RECYCLE_BIN_RETENTION_DAYS + 1)
    recent_time = datetime.now() - timedelta(days=RECYCLE_BIN_RETENTION_DAYS - 1)

    for title, deleted_time in (("旧任务", old_time), ("新任务", recent_time)):
        db.connection.execute(
            """
            INSERT INTO deleted_tasks (
                original_task_id, title, content, status, create_time, update_time,
                due_date, priority, category, reminder_sent, deleted_time
            )
            VALUES (?, ?, '', 0, ?, ?, '2026-07-19', 0, '默认', 0, ?)
            """,
            (
                None,
                title,
                deleted_time.strftime("%Y-%m-%d %H:%M:%S"),
                deleted_time.strftime("%Y-%m-%d %H:%M:%S"),
                deleted_time.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
    db.connection.commit()

    purged = db.purge_expired_deleted_tasks(now=datetime.now())
    assert purged == 1
    assert [task.title for task in db.get_deleted_tasks()] == ["新任务"]
    db.close()


def test_due_reminder_tasks_trigger_once_inside_threshold(tmp_path):
    db = TaskDatabase(db_dir=str(tmp_path))
    task_id = db.add_task(
        title="今晚提交",
        due_date="2026-07-19",
        priority=2,
        category="工作",
    )
    now = datetime(2026, 7, 19, 23, 50, 0)

    due_tasks = db.get_due_reminder_tasks(now=now, threshold_minutes=15)
    assert [task.id for task in due_tasks] == [task_id]

    db.mark_reminder_sent(task_id)
    assert db.get_due_reminder_tasks(now=now, threshold_minutes=15) == []
    db.close()


def test_reminder_threshold_setting_is_configurable_and_clamped(tmp_path):
    db = TaskDatabase(db_dir=str(tmp_path))
    assert db.get_reminder_threshold_minutes() == 15

    db.set_reminder_threshold_minutes(30)
    assert db.get_reminder_threshold_minutes() == 30

    db.set_reminder_threshold_minutes(0)
    assert db.get_reminder_threshold_minutes() == 1

    db.set_reminder_threshold_minutes(99999)
    assert db.get_reminder_threshold_minutes() == 1440
    db.close()
