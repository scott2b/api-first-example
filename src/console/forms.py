from datetime import timedelta
from wtforms import Form, StringField, validators, PasswordField, HiddenField
from common.models import User


class CSRFForm(Form):
    """Base class for forms requiring CSRF protcection. Since CSRF is handled in
    middleware, this should effectively be all form classes.

    Implementing subclasses must have a `request` property that is the current
    request object which, via asgi_csrf middleware, has "csrftoken" in its scope.

    Note that WTForms provides a non-middleware form-centric approach to CSRF (see:
    https://wtforms.readthedocs.io/en/3.0.x/csrf/). However, the current approach is
    used in order to handle CSRF in middleware and to make it consistent with the way
    ajax CSRF is handled in the API.
    """
    csrftoken = HiddenField(name="csrftoken")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.csrftoken.data = self.request.scope["csrftoken"]()
        except AttributeError:
            raise NotImplementedError(
                "Subclasses of CSRFForm must have a request property with scope containing csrftoken."
            )


#class TokenForm(CSRFForm):
#
#    def __init__(self, request, *args, **kwargs):
#        self.request = request
#        super().__init__(*args, **kwargs)


class LoginForm(CSRFForm):
    username = StringField('Username')
    password = PasswordField('Password')

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def validate_password(form, field):
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
