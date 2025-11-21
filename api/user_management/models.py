from django.db import models
import uuid

# Create your models here.
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from django.db import models


class UserManager(BaseUserManager):

    def create_user(self, username, email, password=None, **extra_fields):

        if username is None:
            raise TypeError("Users should have a unsername")
        if email is None:
            raise TypeError("Users should have a Email")
        if password is None:
            raise TypeError("Password is required")
        # if not extra_fields.get("is_oauth") and password is None:
        #     raise TypeError("Password is required")
        # if extra_fields.get("is_oauth") and not extra_fields.get("provider"):
        #     raise TypeError("Oauth authentication method requires a provider")

        user = self.model(username=username, email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        if username is None:
            raise TypeError("Superusers should have an email")
        if email is None:
            raise TypeError("Superusers should have a Email")
        if password is None:
            raise TypeError("Password should not be none")

        user = self.create_user(username, email, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        primary_key=True, unique=True, default=uuid.uuid4, editable=False
    )
    username = models.CharField(  
        max_length=64,
        unique=True
        )
    email = models.EmailField(
        max_length=255,
        unique=True,
    )
    password = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    # is_oauth = models.BooleanField(default=False)
    # provider = models.CharField(max_length=100, blank=True, null=True)
    # password_reset_token = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"

    objects = UserManager()

    def __str__(self):
        return f"User: {self.username} ({self.email})"
    
