from django.db import models

# Create your models here.
from core.mixins import TimeStampMixin


class AccountOwner(TimeStampMixin):
    class Meta:
        abstract = True
