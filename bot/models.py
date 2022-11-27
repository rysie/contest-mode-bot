import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Submission(models.Model):
    objects = models.Manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey('Redditor', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(null=False)
    currently_promoted = models.BooleanField(null=False, default=False)
    deleted = models.BooleanField(default=False)
    original_flair_template_id = models.CharField(max_length=64, null=True, blank=True)
    submission_id = models.CharField(max_length=64, null=False, blank=False)
    subreddit = models.ForeignKey('Subreddit', on_delete=models.CASCADE, null=False)
    title = models.CharField(max_length=256, null=False, blank=False)
    upvotes = models.IntegerField(null=False, default=0)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _('Submission')
        verbose_name_plural = _('Submissions')


class Redditor(models.Model):
    objects = models.Manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, null=False, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Redditor')
        verbose_name_plural = _('Redditors')


class Subreddit(models.Model):
    objects = models.Manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, null=False, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Watched Sub')
        verbose_name_plural = _('Watched Subs')
