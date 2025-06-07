

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange
try:
    # WTForms >=3 removed the html5 module; fall back to new location
    from wtforms.fields import EmailField
except ImportError:  # pragma: no cover - fallback for WTForms<3
    from wtforms.fields.html5 import EmailField


class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class QuantityForm(FlaskForm):
    quantity = IntegerField('Quantity',
                            validators=[DataRequired(), NumberRange(min=1, message="Min 1")])
    submit = SubmitField('Update')


class CheckoutForm(FlaskForm):
    # For simplicity: no address fields if pickup from branch
    submit = SubmitField('Place Order')
