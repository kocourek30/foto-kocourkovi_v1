from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.accounts.managers import UserManager
from apps.common.models import TimeStampedModel


class User(TimeStampedModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email", unique=True)
    first_name = models.CharField("jméno", max_length=150, blank=True)
    last_name = models.CharField("příjmení", max_length=150, blank=True)
    is_staff = models.BooleanField("je zaměstnanec", default=False)
    is_active = models.BooleanField("aktivní", default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "uživatel"
        verbose_name_plural = "uživatelé"

    def __str__(self) -> str:
        return self.email

