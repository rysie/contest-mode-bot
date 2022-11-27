# Register your models here.
from django.contrib import admin
from django.utils.html import format_html

from .models import Submission


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('submission_id', 'title', 'created_at', 'author', 'upvotes', 'deleted')


class SubredditAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class RedditorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_link')

    def user_link(self, obj):
        return format_html(
            '<a href=\'https://reddit.com/u/{username}\' target=\'blank\' rel=\'noreferer noopener\'>'
            'https://reddit.com/u/{username}'
            '</a>',
            username=obj.name
        )

    user_link.allow_tags = True
    user_link.short_description = 'Profile'


class FlairAdmin(admin.ModelAdmin):
    list_display = ('name', 'subreddit')


admin.site.register(Submission, SubmissionAdmin)
# admin.site.register(Redditor, RedditorAdmin)
# admin.site.register(Subreddit, SubredditAdmin)
