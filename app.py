from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-12345'  # Секретний ключ для захисту сесій
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Наша локальна база даних
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ====== МОДЕЛІ БАЗИ ДАНИХ (ТАБЛИЦІ) ======

# 1. Таблиця користувачів (ваших друзів)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    ratings = db.relationship('Rating', backref='author', lazy=True)


# 2. Таблиця продуктів (віскі або сигари)
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(20), nullable=False)  # 'whiskey' або 'cigar'
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(300), nullable=True)  # Шлях до фото
    ratings = db.relationship('Rating', backref='item', lazy=True)


# 3. Таблиця оцінок та відгуків
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)  # Оцінка від 1 до 10
    comment = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ====== МАРШРУТИ (СТОРІНКИ САЙТУ) ======

# Головна сторінка зі списками віскі та сигар
@app.route('/')
def index():
    whiskeys = Item.query.filter_by(category='whiskey').all()
    cigars = Item.query.filter_by(category='cigar').all()
    return render_template('index.html', whiskeys=whiskeys, cigars=cigars)


# Сторінка реєстрації нового користувача
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Таке ім\'я вже зайняте іншим цінителем!', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Ви успішно зареєстровані в клубі! Тепер увійдіть.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# Сторінка входу
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Вітаємо в клубі, {username}! Приємного вечора.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Невірний нікнейм або пароль. Спробуйте ще раз.', 'error')

    return render_template('login.html')


# Логаут (вихід)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Ви вийшли з аккаунту.', 'success')
    return redirect(url_for('index'))


# Автоматичне створення бази даних при першому запуску додатку
with app.app_context():
    db.create_all()


# Кабінет користувача
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


if __name__ == '__main__':
    app.run(debug=True)