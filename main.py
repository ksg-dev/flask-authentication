from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'

# CREATE DATABASE


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Flask-Login Config
login_manager = LoginManager()
login_manager.init_app(app)

# CREATE TABLE IN DB


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))


with app.app_context():
    db.create_all()


# Flask-Login user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

@app.route('/')
def home():
    return render_template("index.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":

        entered_email = request.form.get("email")
        user = db.session.execute(db.select(User).where(User.email == entered_email)).scalar()
        if user:
            flash("That email is already registered. Login instead")
            return redirect(url_for("login"))

        else:
            hashed_pw = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
            new_user = User(
                email=request.form.get("email"),
                name=request.form.get("name"),
                password=hashed_pw,
            )

            db.session.add(new_user)
            db.session.commit()

            # Login and authenticate user after adding details to db
            login_user(new_user)

            return render_template("secrets.html", logged_in=True)
    return render_template("register.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)

                return redirect(url_for('secrets', logged_in=True))

            else:
                flash("Email/Password combination incorrect")
                return redirect(url_for("login"))
        else:
            flash("We have no record of that email. Please try again")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route('/secrets')
@login_required
def secrets():
    return render_template("secrets.html", name=current_user.name)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route('/download')
@login_required
def download():
    return send_from_directory(
        'static', 'files/cheat_sheet.pdf'
    )


if __name__ == "__main__":
    app.run(debug=True)
