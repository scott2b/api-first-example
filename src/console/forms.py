from datetime import timedelta
from wtforms import Form, StringField, validators, PasswordField
from wtforms.csrf.session import SessionCSRF
from common.config import settings
from common.models import User


class CSRFForm(Form):

    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = settings.CSRF_KEY.encode()
        csrf_time_limit = timedelta(minutes=20)

    def validate(self):
        valid = super().validate()
        if valid:
            del self.csrf_token
        return valid


class TokenForm(CSRFForm):

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)


class LoginForm(CSRFForm):
    username = StringField('Username')
    password = PasswordField('Password')

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def validate_password(form, field):
        #_user = User.get(form.username.data)
        _user = User.get_by_username(form.username.data)
        if _user is None:
            raise validators.ValidationError('Incorrect username or password')
        elif not _user.active:
            raise validators.ValidationError(
                'This account has been administratively deactivated. '\
                'Please contact technical support.')
        form.user = _user

    def validate(self):
        super().validate()
        return self.user   

