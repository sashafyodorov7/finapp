from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, date
from sqlalchemy.orm import relationship
import secrets
import string
import os
from sqlalchemy import func
from sqlalchemy.sql.expression import extract
from sqlalchemy import and_, or_
import calendar

app = Flask(__name__)
app.static_folder = 'static'

secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
app.secret_key = secret_key

# Получите текущую директорию проекта
project_directory = os.getcwd()

# Создайте абсолютный путь к базе данных
database_path = os.path.join(project_directory, 'finance.db')

# Подключение к базе данных SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float)
    date = db.Column(db.Date, default=None)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = relationship("Category", back_populates="transactions")

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    is_income = db.Column(db.Boolean, default=False)
    transactions = db.relationship("Transaction", back_populates="category")

class Month(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    years = db.relationship("MonthYear", back_populates="month")  # Добавьте это свойство

    def __init__(self, name):
        self.name = name

class Year(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)
    months = db.relationship("MonthYear", back_populates="year")  # Добавьте это свойство

    def __init__(self, value):
        self.value = value

class MonthYear(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year_id = db.Column(db.Integer, db.ForeignKey('year.id'))
    month_id = db.Column(db.Integer, db.ForeignKey('month.id'))

    year = db.relationship("Year", back_populates="months")
    month = db.relationship("Month", back_populates="years")

with app.app_context():
    db.create_all()

def add_years_and_monthyears():
    with app.app_context():
    # Создайте 12 месяцев и добавьте их в базу данных, если они ещё не существуют
        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        for month in months:
            month_in_db = Month.query.filter_by(name=month).first()
        if not month_in_db:
            month_in_db = Month(name=month)
            db.session.add(month_in_db)
            db.session.commit()

    # Создайте годы с 2023 по 2030 и добавьте их в базу данных, если они ещё не существуют
    for year_value in range(2023, 2031):
        year_in_db = Year.query.filter_by(value=year_value).first()
        if not year_in_db:
            year_in_db = Year(value=year_value)
            db.session.add(year_in_db)
            db.session.commit()

    # Создайте связи между месяцами и годами
    for year in Year.query.all():
        for month in Month.query.all():
            month_year_in_db = MonthYear.query.filter_by(year=year, month=month).first()
            if not month_year_in_db:
                month_year_in_db = MonthYear(year=year, month=month)
                db.session.add(month_year_in_db)
                db.session.commit()


    with app.app_context():
        add_years_and_monthyears()


def get_month_names():
    return ['All month', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

def add_months():
    # Создайте список месяцев
    month_names = get_month_names()

    # Добавьте уникальные месяцы в базу данных
    for month_name in month_names:
        month = Month.query.filter_by(name=month_name).first()
        if not month:
            month = Month(name=month_name)
            db.session.add(month)
            db.session.commit()

with app.app_context():
    add_months()

@app.route('/')
def index():
    transactions = Transaction.query.all()
    today = datetime.now().date()
    categories = Category.query.all()  # Получите все категории из базы данных
    return render_template('index.html', transactions=transactions, today=today, categories=categories)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    description = request.form['description']
    amount = request.form['amount']
    date_str = request.form['date']
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    category_id = request.form['category_id']  # Получите категорию из формы
    if description and amount:
        transaction = Transaction(description=description, amount=amount, date=date, category_id=category_id)
        db.session.add(transaction)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET'])
def dashboard():
    selected_month_year = request.args.get('month', '0-0')
    if '-' in selected_month_year:
        selected_month_year = selected_month_year.split('-')
        selected_month = int(selected_month_year[0])
        selected_year = int(selected_month_year[1])
    else:
        selected_month = 0
        selected_year = 0

    # Остальной код функции остается без изменений
    months = Month.query.all()
    years = Year.query.all()

    if selected_month == 0 and selected_year == 0:
        # Если выбраны "All month" и "All years", не применяйте фильтры по месяцу и году
        transactions = Transaction.query.all()
    else:
        # В противном случае, примените фильтры
        if selected_month == 0:
            # Если выбран "All month", примените фильтр только по году
            transactions = Transaction.query.filter(
                extract('year', Transaction.date) == selected_year
            ).all()
        elif selected_year == 0:
            # Если выбран "All years", примените фильтр только по месяцу
            transactions = Transaction.query.filter(
                extract('month', Transaction.date) == selected_month
            ).all()
        else:
            # В противном случае, примените фильтры и по месяцу, и по году
            first_day_of_selected_month = date(selected_year, selected_month, 1)
            last_day_of_selected_month = date(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1])
            transactions = Transaction.query.filter(
                and_(
                    Transaction.date >= first_day_of_selected_month,
                    Transaction.date <= last_day_of_selected_month
                )
            ).all()

    # Получите доходы и расходы за выбранный месяц и год
    income = db.session.query(func.sum(Transaction.amount)).filter(
        extract('month', Transaction.date) == selected_month,
        extract('year', Transaction.date) == selected_year,
        Transaction.category.has(Category.is_income == True)
    ).scalar()

    expenses = db.session.query(func.sum(Transaction.amount)).filter(
        extract('month', Transaction.date) == selected_month,
        extract('year', Transaction.date) == selected_year,
        Transaction.category.has(Category.is_income == False)
    ).scalar()

    if income is None:
        income = 0

    if expenses is None:
        expenses = 0

        delta = income - expenses

        return render_template('dashboard.html', 
        selected_month=selected_month,
        selected_year=selected_year,
        months=months,
        years=years,
        income=income,
        expenses=expenses,
        delta=delta)

    selected_month = int(request.args.get('month', 0))  # Значение по умолчанию 0 для "All month"
    selected_year = int(request.args.get('year', 0))  # Значение по умолчанию 0 для "All years"

    months = Month.query.all()
    years = Year.query.all()

    if selected_month == 0 and selected_year == 0:
        # Если выбраны "All month" и "All years", не применяйте фильтры по месяцу и году
        transactions = Transaction.query.all()
    else:
        # В противном случае, примените фильтры
        if selected_month == 0:
            # Если выбран "All month", примените фильтр только по году
            transactions = Transaction.query.filter(
                extract('year', Transaction.date) == selected_year
            ).all()
        elif selected_year == 0:
            # Если выбран "All years", примените фильтр только по месяцу
            transactions = Transaction.query.filter(
                extract('month', Transaction.date) == selected_month
            ).all()
        else:
            # В противном случае, примените фильтры и по месяцу, и по году
            first_day_of_selected_month = date(selected_year, selected_month, 1)
            last_day_of_selected_month = date(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1])
            transactions = Transaction.query.filter(
                and_(
                    Transaction.date >= first_day_of_selected_month,
                    Transaction.date <= last_day_of_selected_month
                )
            ).all()

    # Получите доходы и расходы за выбранный месяц и год
        income = db.session.query(func.sum(Transaction.amount)).filter(
        extract('month', Transaction.date) == selected_month,
        extract('year', Transaction.date) == selected_year,
        Transaction.category.has(Category.is_income == True)
    ).scalar()

        expenses = db.session.query(func.sum(Transaction.amount)).filter(
        extract('month', Transaction.date) == selected_month,
        extract('year', Transaction.date) == selected_year,
        Transaction.category.has(Category.is_income == False)
    ).scalar()

    if income is None:
        income = 0

    if expenses is None:
        expenses = 0

    delta = income - expenses
        
    return render_template('dashboard.html', 
        selected_month=selected_month,
        selected_year=selected_year,
        months=months,
        years=years,
        income=income,
        expenses=expenses,
        delta=delta)

@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    categories = Category.query.all()
    if request.method == 'POST':
        name = request.form['name']
        is_income = request.form.get('is_income') == 'true'

        if name:
            category = Category(name=name, is_income=is_income)
            db.session.add(category)
            db.session.commit()
            flash('Category added successfully')
            return redirect(url_for('index'))
        else:
            flash('Category name is required')

    return render_template('add_category.html', categories=categories)

@app.route('/delete_category/<int:id>', methods=['POST'])
def delete_category(id):
    category = Category.query.get(id)
    if category:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully')

    categories = Category.query.all()
    return render_template('add_category.html', categories=categories)

if __name__ == '__main__':
    app.run()