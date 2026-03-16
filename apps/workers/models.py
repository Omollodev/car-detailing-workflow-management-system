"""
WorkerProfile model for managing worker details and performance metrics.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class WorkerProfile(models.Model):
    """
    Extended profile for workers with skills, availability, and performance metrics.
    
    This model is linked one-to-one with the User model for users with the 'worker' role.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='worker_profile',
        verbose_name=_('User Account')
    )
    
    skills = models.ManyToManyField(
        'services.Service',
        blank=True,
        related_name='skilled_workers',
        verbose_name=_('Skills'),
        help_text=_('Services this worker can perform')
    )
    
    is_available = models.BooleanField(
        default=True,
        verbose_name=_('Available'),
        help_text=_('Whether worker is available for job assignment')
    )
    
    current_job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_worker_set',
        verbose_name=_('Current Job'),
        help_text=_('Job the worker is currently working on')
    )
    
    # Performance metrics
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_('Average Rating'),
        help_text=_('Average rating from 0 to 5')
    )
    
    total_ratings = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total Ratings'),
        help_text=_('Number of ratings received')
    )
    
    total_jobs_completed = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Jobs Completed'),
        help_text=_('Total number of jobs completed')
    )
    
    average_completion_time = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Avg Completion Time (minutes)'),
        help_text=_('Average time to complete a job')
    )
    
    employee_id = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Employee ID'),
        help_text=_('Internal employee identifier')
    )
    
    hired_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date Hired')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Additional notes about this worker')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Worker Profile')
        verbose_name_plural = _('Worker Profiles')
        ordering = ['user__first_name', 'user__last_name']
    
    def __str__(self) -> str:
        return f"{self.user.get_full_name() or self.user.username} - Worker"
    
    @property
    def name(self) -> str:
        """Return worker's full name."""
        return self.user.get_full_name() or self.user.username
    
    @property
    def formatted_rating(self) -> str:
        """Return rating formatted with star symbol."""
        if self.total_ratings == 0:
            return "No ratings"
        return f"{self.rating:.1f}/5.0 ({self.total_ratings} ratings)"
    
    @property
    def is_busy(self) -> bool:
        """Check if worker is currently working on a job."""
        return self.current_job is not None
    
    def can_perform_service(self, service) -> bool:
        """Check if worker has the skill to perform a specific service."""
        return service in self.skills.all()
    
    def get_assigned_jobs(self):
        """Return all jobs assigned to this worker (non-completed)."""
        return self.assigned_jobs.exclude(status__in=['completed', 'cancelled'])
    
    def get_completed_jobs(self):
        """Return all jobs completed by this worker."""
        return self.assigned_jobs.filter(status='completed')
    
    def get_job_count_today(self):
        """Return number of jobs completed today."""
        from django.utils import timezone
        today = timezone.now().date()
        return self.assigned_jobs.filter(
            status='completed',
            completed_at__date=today
        ).count()
    
    def update_performance_metrics(self):
        """
        Update performance metrics based on completed jobs.
        Called after a job is completed.
        """
        completed_jobs = self.get_completed_jobs()
        self.total_jobs_completed = completed_jobs.count()
        
        # Calculate average completion time
        jobs_with_times = completed_jobs.filter(
            actual_duration__isnull=False
        )
        if jobs_with_times.exists():
            total_time = sum(job.actual_duration for job in jobs_with_times)
            self.average_completion_time = total_time // jobs_with_times.count()
        
        self.save(update_fields=['total_jobs_completed', 'average_completion_time'])
    
    def add_rating(self, new_rating: float):
        """
        Add a new rating and recalculate the average.
        
        Args:
            new_rating: Rating value from 0 to 5
        """
        if not 0 <= new_rating <= 5:
            raise ValueError("Rating must be between 0 and 5")
        
        # Calculate new average
        total = float(self.rating) * self.total_ratings
        self.total_ratings += 1
        self.rating = Decimal(str((total + new_rating) / self.total_ratings))
        self.save(update_fields=['rating', 'total_ratings'])
    
    def set_current_job(self, job):
        """Assign a job as the current job and mark as busy."""
        self.current_job = job
        self.is_available = False
        self.save(update_fields=['current_job', 'is_available'])
    
    def clear_current_job(self):
        """Clear current job and mark as available."""
        self.current_job = None
        self.is_available = True
        self.save(update_fields=['current_job', 'is_available'])
    
    @classmethod
    def get_available_workers(cls):
        """Return all available workers."""
        return cls.objects.filter(
            is_available=True,
            user__is_active=True,
            user__is_active_worker=True
        )
    
    @classmethod
    def get_best_available_worker(cls, service=None):
        """
        Get the best available worker, optionally filtered by service skill.
        
        Prioritizes workers with:
        1. Required skill (if service specified)
        2. Higher rating
        3. Fewer jobs completed today (workload balancing)
        """
        workers = cls.get_available_workers()
        
        if service:
            workers = workers.filter(skills=service)
        
        if not workers.exists():
            return None
        
        # Sort by rating (desc), then by jobs today (asc)
        return sorted(
            workers,
            key=lambda w: (-float(w.rating), w.get_job_count_today())
        )[0]
