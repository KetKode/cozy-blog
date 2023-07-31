from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import StringField, SubmitField, DateField, PasswordField, TextAreaField, SelectField
from wtforms.validators import DataRequired, URL


class NewPostForm(FlaskForm):
    title = StringField("Title of your post", validators=[DataRequired()])
    subtitle = StringField("Subtitle of your post", validators=[DataRequired()])
    body = CKEditorField("Write your post here", validators=[DataRequired()])
    date = DateField("What date is it today?", validators=[DataRequired()])

    image_url = StringField("Please provide a URL to an image", validators=[DataRequired(), URL()])
    tag = SelectField("What is the topic of the post?", choices=["🔋️ well-being", "🐈‍⬛ pets", "🫐 nutrition",
                                                                 "💕 relationships", "👩🏻‍💻 work-life balance"], validators=[DataRequired()])

    submit = SubmitField ("Submit post!", render_kw={"style": "text-transform: uppercase;"})


class RegisterForm(FlaskForm):
    name = StringField("What's your name?", validators=[DataRequired()])
    email = StringField("What's your email?", validators=[DataRequired()])
    password = PasswordField("Create a strong password", validators=[DataRequired()])
    submit = SubmitField("Register", render_kw={"style": "text-transform: uppercase;"})


class LoginForm(FlaskForm):
    email = StringField("What's your email?", validators=[DataRequired()])
    password = PasswordField("What's your password?", validators=[DataRequired()])
    submit = SubmitField("Log in", render_kw={"style": "text-transform: uppercase;"})


class ContactForm(FlaskForm):
    email = StringField("What's your email?", validators=[DataRequired()])
    name = StringField("What's your name?", validators=[DataRequired()])
    message = TextAreaField("Type your question here", validators=[DataRequired()])
    submit = SubmitField("Send!", render_kw={"style": "text-transform: uppercase;"})


class CommentForm(FlaskForm):
    body = CKEditorField("", validators=[DataRequired()])
    submit = SubmitField("Leave comment!", render_kw={"style": "text-transform: uppercase;"})