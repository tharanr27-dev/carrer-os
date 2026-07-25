"""Background task readiness tests that do not require a running worker."""

from app.modules.admin.tasks import celery_app
from app.modules.community.tasks import moderate_post_background
from app.modules.placements.tasks import (
    analyze_batch_readiness_background,
    calculate_drive_eligibility_background,
    rank_students_for_drive_background,
)
from app.modules.recruiters.tasks import generate_candidate_insights_background


def test_admin_celery_app_has_required_periodic_jobs_registered():
    schedule = celery_app.conf.beat_schedule

    assert "admin-health-snapshot" in schedule
    assert "admin-dashboard-refresh" in schedule
    assert "admin-ai-token-aggregation" in schedule
    assert "admin-moderation-cleanup" in schedule


def test_enterprise_background_tasks_expose_delay_interface():
    tasks = [
        moderate_post_background,
        calculate_drive_eligibility_background,
        rank_students_for_drive_background,
        analyze_batch_readiness_background,
        generate_candidate_insights_background,
    ]

    assert all(hasattr(task, "delay") for task in tasks)
    assert all(task.name for task in tasks)
