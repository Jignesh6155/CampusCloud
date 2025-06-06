from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    # Use student_number as the identifier
    student_number = StringField('Student Number', validators=[DataRequired(), Length(max=50)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Sign In')

class SignupForm(FlaskForm):
    student_number = StringField('Student Number', validators=[DataRequired(), Length(max=50)])
    email = StringField('Student Email', validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField('Display Name', validators=[Length(max=100)])  # Optional
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Create Account')