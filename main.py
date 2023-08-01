from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_sqlalchemy import SQLAlchemy
from posts import posts
from flask_ckeditor import CKEditor
from forms import NewPostForm, RegisterForm, LoginForm, ContactForm, CommentForm
from flask_bootstrap import Bootstrap5
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import hashlib
import random


app = Flask(__name__)
ckeditor = CKEditor(app)
bootstrap = Bootstrap5(app)

# login manager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# connect to database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///articles.db'
app.config['SECRET_KEY'] = "my super secret key"
db = SQLAlchemy(app)


# a user loader callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Gravatar settings


def gravatar(email, size=80):
    # Gravatar URL is based on MD5 hash of the lowercase email address
    hash_email = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{hash_email}?s={size}&d=retro"


# Articles table configuration


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), unique=True, nullable=False)
    author = db.Column(db.String(50), nullable=True)
    body = db.Column(db.String(1000), unique=True, nullable=False)
    date = db.Column(db.String(10), nullable=False)
    image_url = db.Column(db.String(10), nullable=False)
    tag = db.Column(db.String(10), nullable=False)

    # relationships

    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment', backref='parent_post')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

    # relationships

    posts = db.relationship('Post', backref='poster')
    comments = db.relationship('Comment', backref='comment_author')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    # relationships

    comment_author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    post = db.relationship('Post', backref='favorites')


with app.app_context():
    db.create_all()

    # for post_data in posts:
    #     post = Post(
    #         title=post_data["title"],
    #         subtitle=post_data["subtitle"],
    #         author=post_data["author"],
    #         body=post_data["body"],
    #         date=post_data["date"],
    #         image_url=post_data["image_url"],
    #         tag=post_data["tag"]
    #         )
    #
    #     db.session.add(post)
    #
    # db.session.commit()


@app.route("/", methods=['GET', 'POST'])
def home():
    all_posts = Post.query.all()
    random.shuffle(all_posts)
    return render_template("index.html", posts=all_posts)


@app.route("/categories")
def categories():
    tag_list = []
    for post in posts:
        tag = post.get("tag")
        if tag:
            tag_list.append(tag)
            tag_set = set(tag_list)
            tags = list(tag_set)

    return render_template("categories.html", tags=tags, posts=posts)


@app.route("/favorite/<int:post_id>", methods=['GET', 'POST'])
@login_required
def toggle_favorite(post_id):
    post = Post.query.get(post_id)
    favorite = Favorite.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        flash("Post is removed from your favourites!")
        is_favorited = False
    else:
        favorite = Favorite(user_id=current_user.id, post_id=post_id)
        db.session.add(favorite)
        db.session.commit()
        flash("Post is added to your favourites.")
        is_favorited = True

    session['is_favorited'] = is_favorited
    return redirect(url_for('show_post', post_id=post_id))


@app.route("/register", methods=['GET', 'POST'])
def register():

    form = RegisterForm()

    if form.validate_on_submit():

        # if email already exists

        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with this email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(password=form.password.data,
                                                          method="pbkdf2:sha256:600000", salt_length=8)

        new_user = User(email=form.email.data,
                        name=form.name.data,
                        password=hash_and_salted_password)

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template("register.html", form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # find user by email

        user = User.query.filter_by(email=email).first()

        # email doesn't exist

        if not user:
            flash("Email doesn't exist, try again!")
            return redirect(url_for('login'))

        # incorrect password

        elif not check_password_hash(user.password, password):
            flash("Password incorrect, try again!")
            return redirect(url_for('login'))

        # check stored password hash against entered password hash

        # everything is correct

        else:
            login_user(user)
            flash("Login successful!")
            return redirect(url_for('dashboard', gravatar=gravatar))
    return render_template("login.html", form=form)


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()

    all_posts = Post.query.all()
    random.shuffle(all_posts)

    random_posts_to_read = all_posts[:4]

    user = User.query.get(current_user.id)
    user_posts = user.posts

    return render_template("dashboard.html", gravatar=gravatar, favorites=favorites,
                           random_posts_to_read=random_posts_to_read, user_posts=user_posts, user=user)


@app.route("/admin")
@login_required
def admin():
    id = current_user.id
    if id == 1:
        return render_template("admin.html")
    else:
        flash("Sorry, you must be the admin to view this page.")
        return redirect(url_for('dashboard'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        email = form.email.data
        name = form.email.data
        message = form.message.data

    return render_template("contact.html", form=form)


@app.route("/new-post", methods=["GET", "POST"])
@login_required
def make_post():
    form = NewPostForm()
    if form.validate_on_submit():
        poster = current_user.id
        new_post = Post(
            title=form.title.data,
            subtitle=form.subtitle.data,
            poster_id=poster,
            body=form.body.data,
            date=form.date.data,
            image_url=form.image_url.data,
            tag=form.tag.data
            )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    requested_post = Post.query.get(post_id)
    form = NewPostForm(
        title=requested_post.title,
        subtitle=requested_post.subtitle,
        image_url=requested_post.image_url,
        author=requested_post.author,
        body=requested_post.body.data,
        tag=requested_post.tag.data,
        )

    if form.validate_on_submit():
        requested_post.title = form.title.data
        requested_post.subtitle = form.subtitle.data
        requested_post.body = form.body.data
        requested_post.image_url = form.image_url.data
        requested_post.tag = requested_post.tag.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("make-post.html", post=requested_post, form=form)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = Post.query.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment_text = form.body.data
        new_comment = Comment(text=comment_text, comment_author=current_user, post_id=post_id)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id))

    return render_template("post.html", post=requested_post, form=form, gravatar=gravatar)


@app.route("/delete-comment/<int:post_id>/<int:comment_id>", methods=["GET", "POST"])
@login_required
def delete_comment(comment_id, post_id):
    comment_to_delete = Comment.query.get(comment_id)
    post_id = comment_to_delete.post_id

    # Check if the comment exists and the current user is the author of the comment
    if comment_to_delete.comment_author_id != current_user.id:
        flash("You are not authorized to delete this comment.", "error")
        return redirect(url_for('show_post', post_id=post_id))

    else:
        db.session.delete(comment_to_delete)
        db.session.commit()
        flash("Comment deleted successfully.", "success")
        return redirect(url_for('show_post', post_id=post_id))


@app.route("/delete/<post_id>")
@login_required
def delete_post(post_id):
    requested_post = Post.query.get(post_id)
    id = current_user.id
    if id == requested_post.poster.id:
        db.session.delete(requested_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("index.html", post=requested_post)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=4500, debug=False)

