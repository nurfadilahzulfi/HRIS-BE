from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email wajib diisi')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.SUPER_ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        HR_MANAGER  = 'HR_MANAGER',  'HR Manager'
        HR_STAFF    = 'HR_STAFF',    'HR Staff'
        MANAGER     = 'MANAGER',     'Manager'
        EMPLOYEE    = 'EMPLOYEE',    'Employee'

    email      = models.EmailField(unique=True, verbose_name='Email')
    role       = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        verbose_name='Role',
    )

    # Linked to employee profile (set after employee is created)
    # NOTE: Uses string reference to avoid circular import — Employee model
    # is defined in apps.employees which is registered after apps.core.
    employee   = models.OneToOneField(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_account',
        verbose_name='Employee',
    )

    # Scoped to a specific entity for access control
    entity     = models.ForeignKey(
        'company.Entity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Entity',
    )

    is_active  = models.BooleanField(default=True, verbose_name='Active')
    is_staff   = models.BooleanField(default=False, verbose_name='Staff')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Date Joined')

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['email']

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        if self.employee:
            return self.employee.full_name
        return self.email

    @property
    def is_hr(self):
        return self.role in [self.Role.HR_MANAGER, self.Role.HR_STAFF, self.Role.SUPER_ADMIN]

    @property
    def is_manager_or_above(self):
        return self.role in [
            self.Role.MANAGER,
            self.Role.HR_MANAGER,
            self.Role.SUPER_ADMIN,
        ]
