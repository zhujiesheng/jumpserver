import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, ugettext as __
from rest_framework.authtoken.models import Token
from django.conf import settings

from common.mixins.models import CommonModelMixin
from common.utils import get_object_or_none, get_request_ip, get_ip_city


class AccessKey(models.Model):
    id = models.UUIDField(verbose_name='AccessKeyID', primary_key=True,
                          default=uuid.uuid4, editable=False)
    secret = models.UUIDField(verbose_name='AccessKeySecret',
                              default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='User',
                             on_delete=models.CASCADE, related_name='access_keys')
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    date_created = models.DateTimeField(auto_now_add=True)

    def get_id(self):
        return str(self.id)

    def get_secret(self):
        return str(self.secret)

    def get_full_value(self):
        return '{}:{}'.format(self.id, self.secret)

    def __str__(self):
        return str(self.id)


class PrivateToken(Token):
    """Inherit from auth token, otherwise migration is boring"""

    class Meta:
        verbose_name = _('Private Token')


class LoginConfirmSetting(CommonModelMixin):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, verbose_name=_("User"), related_name="login_confirm_setting")
    reviewers = models.ManyToManyField('users.User', verbose_name=_("Reviewers"), related_name="review_login_confirm_settings", blank=True)
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))

    @classmethod
    def get_user_confirm_setting(cls, user):
        return get_object_or_none(cls, user=user)

    def create_confirm_ticket(self, request=None):
        from tickets.models import LoginConfirmTicket
        title = _('User login confirm: {}').format(self.user)
        if request:
            remote_addr = get_request_ip(request)
            city = get_ip_city(remote_addr)
            body = _("User: {}\nIP: {}\nCity: {}\nDate: {}\n").format(
                self.user, remote_addr, city, timezone.now()
            )
        else:
            city = 'Localhost'
            remote_addr = '127.0.0.1'
            body = ''
        reviewer = self.reviewers.all()
        reviewer_names = ','.join([u.name for u in reviewer])
        ticket = LoginConfirmTicket.objects.create(
            user=self.user, user_display=str(self.user),
            title=title, body=body,
            city=city, ip=remote_addr,
            assignees_display=reviewer_names,
            type=LoginConfirmTicket.TYPE_LOGIN_CONFIRM,
        )
        ticket.assignees.set(reviewer)
        return ticket

    def __str__(self):
        return '{} confirm'.format(self.user.username)

