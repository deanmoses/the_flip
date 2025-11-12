"""View package that groups auth, report, and machine concerns."""

from . import auth, machines, reports
from .auth import CustomLoginView, home
from .machines import (
    machine_detail,
    machine_list,
    machine_log_create,
    machine_log_detail,
    machine_log_list,
    machine_public_view,
    machine_qr,
    machine_task_create,
    machine_tasks_list,
)
from .reports import (
    problem_report_create,
    report_detail,
    report_list,
    task_create_todo,
)

__all__ = [
    'auth',
    'machines',
    'reports',
    'CustomLoginView',
    'home',
    'machine_detail',
    'machine_list',
    'machine_log_create',
    'machine_log_detail',
    'machine_log_list',
    'machine_public_view',
    'machine_qr',
    'machine_task_create',
    'machine_tasks_list',
    'problem_report_create',
    'report_detail',
    'report_list',
    'task_create_todo',
]

