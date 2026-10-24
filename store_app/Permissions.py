from datetime import date

from rest_framework import permissions


def has_subscription(user):
    # есть ли у пользователя действующая подписка
    if not user.is_authenticated:
        return False
    return user.subscriptions.filter(end_date__gte=date.today()).exists()


class IsAuthorOrReadOnly(permissions.BasePermission):
    # менять и удалять может только автор
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user