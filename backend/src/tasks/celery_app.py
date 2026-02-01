"""
Celery Application Configuration
Author: Sowad Al-Mughni

Async Task Processing
"""

from celery import Celery
import os

# Get broker URL from environment or use default
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')

# Create Celery app
celery_app = Celery(
    'rwa_studio',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        'src.tasks.email_tasks',
        'src.tasks.kyc_tasks',
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,  # Acknowledge tasks after they complete
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Rate limiting
    task_annotations={
        'src.tasks.email_tasks.*': {
            'rate_limit': '10/m'  # 10 emails per minute max
        },
        'src.tasks.kyc_tasks.*': {
            'rate_limit': '5/m'  # 5 KYC operations per minute
        },
    },
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_concurrency=4,  # 4 concurrent workers
)


def init_celery(app):
    """Initialize Celery with Flask app context"""
    
    class ContextTask(celery_app.Task):
        """Celery task that runs within Flask app context"""
        
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery_app.Task = ContextTask
    return celery_app
