"""
Міксін для розмежування доступу до Django Admin за роллю користувача.

Менеджер отримує доступ лише до тих моделей, до яких підключено цей міксін
(замовлення і склад). Каталог і користувачі — тільки для Адміністратора.
"""


class ManagerAccessMixin:
    """
    Підключається до ModelAdmin-класів, які менеджер має право переглядати.
    Без цього міксіну менеджер не побачить модель в адмінці взагалі.
    """

    def _is_manager(self, request):
        return hasattr(request.user, 'role') and request.user.role == 'manager'

    def has_view_permission(self, request, obj=None):
        if self._is_manager(request):
            return True
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        if self._is_manager(request):
            return True
        return super().has_add_permission(request, obj) if obj is not None else super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if self._is_manager(request):
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if self._is_manager(request):
            return True
        return super().has_delete_permission(request, obj)
