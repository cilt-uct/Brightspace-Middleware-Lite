from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, EqualTo, Length

from ..db.models import User


class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    name = StringField(
        'Name', validators=[DataRequired(), Length(min=1, max=255)]
    )
    username = StringField(
        'username', validators=[DataRequired()] #, Length(min=8, max=8)]
    )
    password = PasswordField(
        'Password', validators=[DataRequired()] #, Length(min=6, max=25)]
    )
    confirm = PasswordField(
        'Repeat password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match.')
        ],
    )

    def validate(self, extra_validators=None):
        initial_validation = super().validate(extra_validators)

        if not initial_validation:
            return False

        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append('Username already registered')
            return False
        if self.password.data != self.confirm.data:
            self.password.errors.append('Passwords must match')
            return False

        return True
