"""
apps/core/permissions.py

Sentralisasi seluruh permission class yang dipakai lintas modul.
Import dari sini, jangan definisikan ulang di setiap views.py.

Sebelum refactor: IsHROrReadOnly didefinisikan identik di 8+ file.
Sekarang: satu definisi, import dari satu tempat — konsisten & mudah diubah.
"""
from rest_framework import permissions


class IsHROrReadOnly(permissions.BasePermission):
    """
    Akses tulis (POST/PUT/PATCH/DELETE) hanya untuk HR admin ke atas.
    Akses baca (GET/HEAD/OPTIONS) untuk semua user yang terautentikasi.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_hr


class IsManagerOrHR(permissions.BasePermission):
    """
    Hanya Manager, HR Manager, HR Staff, dan Super Admin.
    Dipakai untuk aksi evaluasi/approval yang tidak boleh dilakukan karyawan biasa.
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_manager_or_above
        )


class IsHR(permissions.BasePermission):
    """
    Hanya HR staff/manager/super_admin — untuk aksi admin murni.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_hr
