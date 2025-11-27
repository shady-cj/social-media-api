from django.db import models
from django.db.models import Q, F
import uuid
from django.contrib.auth import get_user_model
# Create your models here.

User = get_user_model()


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    first_name = models.CharField(max_length=64, null=True, blank=True)
    last_name = models.CharField(max_length=64, null=True, blank=True)
    profile_photo = models.URLField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    preferences = models.JSONField(default=dict, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    class Meta:
        indexes = [
            models.Index(fields=["first_name"], name="idx_profile_first_name"),
            models.Index(fields=["last_name"], name="idx_profile_last_name")
        ]
    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
    def get_mutual_followers(self):
        # return User.objects.filter(
        #     followers__followed_by=self.user,
        #     following__user=self.user,
        # )
        return Profile.objects.filter(
            user__followers__followed_by=self.user,
            user__following__user=self.user
        )
    
    def get_followers(self):
        return Profile.objects.filter(
            user__following__user=self.user
        )
    
    def get_following(self):
        return Profile.objects.filter(
            user__followers__followed_by=self.user
        )


class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    parent_post = models.ForeignKey("self", on_delete=models.CASCADE, related_name="comments", null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False) # soft delete flag

    def likes(self):
        return self.engagements.filter(type="LIKE").count()


class PostMedia(models.Model):
    media_types = (
            ("PHOTO", "Photo"),
            ("VIDEO", "Video"),
            ("GIF", "Gif")
        )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="attachments")
    media_url = models.URLField()
    type = models.CharField(max_length=10, choices=media_types, default="PHOTO")
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    mime_type = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(type__in=['PHOTO','VIDEO','GIF']), name='valid_media_type'),
        ]

class Interaction(models.Model):
    interaction_type = (
        ("LIKE", "Like"),
        ("SHARE", "Share"),
        ("COMMENT", "Comment")
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interactions")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="engagements")
    type = models.CharField(max_length=10, choices=interaction_type, default="LIKE")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(type__in=['LIKE','SHARE','COMMENT']), name='valid_interaction_type'),
        ]
    
    def save(self, *args, **kwargs):
        # Additional logic can be added here
        if self.type == "LIKE":
            # prevent duplicate likes by the same user on the same post
            if Interaction.objects.filter(user=self.user, post=self.post, type="LIKE").exists():
                raise ValueError("User has already liked this post.")
            

        super().save(*args, **kwargs)


class Bookmark(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    bookmarked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_bookmark'),
        ]
        indexes = [
            models.Index(fields=['user', 'post'], name='idx_user_post_bookmark'),
        ]


class Follow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    followed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'followed_by'], name='unique_follow'),
            models.CheckConstraint(
                check=~Q(user=F('followed_by')) ,  # example: type cannot be empty
                name='no_self_follow'
            ),
        ]
        indexes = [
            # Index for queries like: followers__followed_by = user_x
            models.Index(fields=['user', 'followed_by'], name='idx_user_followedby'),

            # reverse index for queries like: following__user = user_x
            models.Index(fields=['followed_by', 'user'], name='idx_followedby_user'),
        ]
