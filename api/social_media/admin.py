from django.contrib import admin
from .models import Profile, Post, PostMedia, Interaction, Follow
# Register your models here.


admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(PostMedia)
admin.site.register(Interaction)
admin.site.register(Follow)