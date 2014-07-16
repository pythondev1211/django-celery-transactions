# coding=utf-8
from functools import partial
import threading

from celery import task as base_task, current_app, Task
from django.db import transaction
from django.db.transaction import get_connection

import djcelery_transactions.transaction_signals

# Thread-local data (task queue).
_thread_data = threading.local()


def _get_task_queue():
    """Returns the calling thread's task queue."""
    return _thread_data.__dict__.setdefault("task_queue", [])


class PostTransactionTask(Task):
    """A task whose execution is delayed until after the current transaction.

    The task's fate depends on the outcome of the current transaction. If it's
    committed or no changes are made in the transaction block, the task is sent
    as normal. If it's rolled back, the task is discarded.

    If transactions aren't being managed when ``apply_asyc()`` is called (if
    you're in the Django shell, for example) or the ``after_transaction``
    keyword argument is ``False``, the task will be sent immediately.

    A replacement decorator is provided:

    .. code-block:: python

        from djcelery_transactions import task

        @task
        def example(pk):
            print "Hooray, the transaction has been committed!"
    """

    abstract = True

    def original_apply_async(self, *args, **kwargs):
        """Shortcut method to reach real implementation
        of celery.Task.apply_sync
        """
        return super(PostTransactionTask, self).apply_async(*args, **kwargs)

    def apply_async(self, *args, **kwargs):
        # Delay the task unless the client requested otherwise or transactions
        # aren't being managed (i.e. the signal handlers won't send the task).
        connection = get_connection()
        if connection.in_atomic_block and not getattr(current_app.conf, 'CELERY_ALWAYS_EAGER', False):
            _get_task_queue().append((self, args, kwargs))
        else:
            return self.original_apply_async(*args, **kwargs)


def _discard_tasks(**kwargs):
    """Discards all delayed Celery tasks.

    Called after a transaction is rolled back."""
    _get_task_queue()[:] = []


def _send_tasks(**kwargs):
    """Sends all delayed Celery tasks.

    Called after a transaction is committed or we leave a transaction
    management block in which no changes were made (effectively a commit).
    """
    queue = _get_task_queue()
    while queue:
        tsk, args, kwargs = queue.pop(0)
        tsk.original_apply_async(*args, **kwargs)


# A replacement decorator.
task = partial(base_task, base=PostTransactionTask)

# Hook the signal handlers up.
transaction.signals.post_commit.connect(_send_tasks)
transaction.signals.post_rollback.connect(_discard_tasks)
