import json
import random
import os
import time
import sys
import binascii
from collections import OrderedDict
from urllib.parse import urlparse
from flask import Flask, request, render_template, redirect, url_for, Response, jsonify
from flask import session 
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField
from wtforms.validators import InputRequired, Email, Length
from wtforms.widgets import TextArea
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Message, Mail
from flask_babel import Babel, gettext
from apscheduler.schedulers.background import BackgroundScheduler
import load_global
import re
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_mail(recipient_mail, subject, body):
    content_html += "<br><p>{}</p><br><p>{}</p>".format(body, recipient_mail)
    message = Mail(
    from_email=os.environ['EMAIL_USER'],
    to_emails=os.environ['EMAIL_USER'],
    subject='{}'.format(subject),
    html_content=content_html)
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code) 
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)



def write_info_grants_json(rss_grants_data_dict_list, rss_news_data_dict_list):
    compiled_data_dict = {}
    with open("data/info_grants.json", 'w', encoding="utf-8") as compiled_data_file:
        compiled_data_dict["grants"] = rss_grants_data_dict_list
        compiled_data_dict["news"] = rss_news_data_dict_list
        json.dump(compiled_data_dict, compiled_data_file)

def add_grants_info():
    rss_grants_data_dict_list, rss_news_data_dict_list = load_global.load_all()
    write_info_grants_json(rss_grants_data_dict_list, rss_news_data_dict_list)

def get_grants_info():
    with open("data/info_grants.json", 'r', encoding="utf-8") as compiled_data_file:
        compiled_data_dict = json.load(compiled_data_file)
    return compiled_data_dict["grants"]

def filter_grants(news_list):
    grants_list = []
    for news_dict in news_list:
        if key_word_exists(news_dict):
            grants_list.append(news_dict)
    return grants_list

def key_word_exists(news_dict):
    key_words = []
    with open("data/filtering_words.json", "r") as key_words_file:
        file_dict = json.load(key_words_file)
        key_words = file_dict["palabras"]
        non_key_words = file_dict["palabras no queridas"]
    text = news_dict["summary"] + " " + news_dict["titulo"] 
    regex = re.compile('[^a-zA-Z]')
    text = regex.sub(' ', text)
    print(text)
    text_words = text.lower().split(" ")
    for non_key_word in non_key_words:
        if non_key_word in text_words:
            return False
    for key_word in key_words:
        if key_word in text_words:
            return True
    return False

def get_news_info():
    with open("data/info_grants.json", 'r', encoding="utf-8") as compiled_data_file:
        compiled_data_dict = json.load(compiled_data_file)
    return compiled_data_dict["news"]

def add_grants_info():
    rss_grants_data_dict_list, rss_news_data_dict_list = load_global.load_all()
    write_info_grants_json(rss_grants_data_dict_list, rss_news_data_dict_list)

def clean_events(events_list):
    title_list = []
    clean_events_list = []
    if events_list:
        for event in events_list:
            title = event["titulo"]
            if title in title_list:
                continue
            else:
                event["summary"] = cleanhtml(event["summary"])
                clean_events_list.append(event)
                title_list.append(title)
    return clean_events_list

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

def ordenar_dates(new_news_list):
    ordered_list_dict = {"2020": {"Dec":[],"Nov":[],"Oct":[],"Sep":[],"Aug":[],"Jul":[],"Jun":[],"May":[],"Apr":[],"Mar":[],"Feb":[],"Jan":[]}, "2019":{"Dec":[],"Nov":[],"Oct":[],"Sep":[],"Aug":[],"Jul":[],"Jun":[],"May":[],"Apr":[],"Mar":[],"Feb":[],"Jan":[]}, "2018":{"Dec":[],"Nov":[],"Oct":[],"Sep":[],"Aug":[],"Jul":[],"Jun":[],"May":[],"Apr":[],"Mar":[],"Feb":[],"Jan":[]}}
    for news_dict in new_news_list:
        date_elements = news_dict["pubDate"].split(" ")
        day = date_elements[1]
        month = date_elements[2]
        year = date_elements[3]
        if year in ordered_list_dict.keys():
            ordered_list_dict[year][month].append(news_dict)
    for year in ordered_list_dict.keys():
        year_dict = ordered_list_dict[year]
        for month in year_dict.keys():
            if year_dict[month]:
                year_dict[month] = sorted(year_dict[month], key = lambda i: i['pubDate'].split(" ")[1], reverse=True)
                print(year_dict[month])
    new_ordered_news_list = []
    for year_key in ordered_list_dict.keys():
        for month_key in ordered_list_dict[year_key].keys():
            for news_dict in ordered_list_dict[year_key][month_key]:
                new_ordered_news_list.append(news_dict)
    return new_ordered_news_list
    

scheduler = BackgroundScheduler()
add_grants_info()
scheduler.add_job(add_grants_info, "interval", seconds=600)
scheduler.start()

app = Flask(__name__)
babel = Babel(app)

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": os.environ['EMAIL_USER'],
    "MAIL_PASSWORD": os.environ['EMAIL_PASSWORD']
}
app.config.update(mail_settings)
app.config.from_object(__name__)
random.seed()
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bug_database.db'
app.config['LANGUAGES'] = {
    'en': 'English',
    'es': 'Español'
}

Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
mail = Mail(app)



class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    nationality = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))


"""--------------------------------------------------------------------------------------------------------------------------------"""
"""-------------------------------------------------------SESSION------------------------------------------------------------------"""
"""--------------------------------------------------------------------------------------------------------------------------------"""

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class LoginForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(
        message='Invalid email'), Length(max=50)])
    password = PasswordField('password', validators=[
                             InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
    name = StringField('Full name', validators=[InputRequired(), Length(max=50)])
    email = StringField('Email', validators=[InputRequired(), Email(
        message='Invalid email'), Length(max=50)])
    nationality = StringField('Nationality', validators=[InputRequired(), Length(max=50)])
    password = PasswordField('password', validators=[
                             InputRequired(), Length(min=8, max=80)])

class ContactForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[InputRequired(), Email(
        message='Invalid email'), Length(max=50)])
    text = StringField('Mensaje', validators=[
                             InputRequired()],widget=TextArea())

@app.route("/")
def index():
    return render_template("homepage.html", name="homepage", session=session)

@app.route("/about_us")
def about_us():
    return render_template("about_us.html", name="about_us", current_user=current_user)

@app.route("/contact_us")
def contact_us():
    form = ContactForm()
    email = form.email.data
    text = form.text.data
    if form.validate_on_submit():
        send_mail(email , "Cliente quiere contactarse", text)
    return render_template("contact_us.html", name="contact_us", current_user=current_user, form=form)

@app.route("/fund_searcher")
def fund_searcher():
    new_grants_list = get_news_info()
    new_grants_list = filter_grants(new_grants_list)
    new_grants_list.sort(key=lambda item:item['pubDate'], reverse=True)
    new_grants_list = ordenar_dates(new_grants_list)
    new_grants_list = clean_events(new_grants_list)
    return render_template("fund_searcher.html", name="fund_searcher", current_user=current_user, new_grants_list=new_grants_list)

@app.route("/matching", methods=['GET', 'POST'])
def matching():
    form = ContactForm()
    email = form.email.data
    text = form.text.data
    print(str(form))
    if form.validate_on_submit():
        send_mail(email , "Cliente quiere contactarse", text)
    return render_template("matching.html", name="matching", current_user=current_user, form=form)

@app.route("/resources")
def resources():
    return render_template("resources.html", name="resources", current_user=current_user)

@app.route("/events")
def events():
    new_news_list = get_news_info()
    new_news_list.sort(key=lambda item:item['pubDate'], reverse=True)
    new_news_list = ordenar_dates(new_news_list)
    new_news_list = clean_events(new_news_list)
    return render_template("events.html", name="events", current_user=current_user, new_news_list=new_news_list)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                session['logged_in'] = True
                login_user(user, remember=form.remember.data)
                return render_template("homepage.html", name="homepage", session=session)
        return '<h2>Invalid email or password</h2>'
    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if not user:
            hashed_password = generate_password_hash(
                form.password.data, method='sha256')
            new_user = Users(email=form.email.data, password=hashed_password, name=form.name.data, nationality=form.nationality.data)
            send_mail(form.name.data, form.email.data,"Welcome to BUG" ,"Welcome to the BUG Creative Industry Network {}".format(form.name.data))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            session['logged_in'] = True
            return render_template("homepage.html", name="homepage", session=session)
        return '<h2>Email already registered</h2>'
        # return '<h1>' + form.email.data + ' ' + form.password.data +'</h1>'
    return render_template('signup.html', form=form)


@app.route('/check/user', methods=['GET'])
def check_credentials_user():
    email = request.args.get('email')
    password = request.args.get("password")
    user = Users.query.filter_by(email=email).first()
    if user:
        if check_password_hash(user.password, password):
            return jsonify({'response': True})
        else:
            return jsonify({'response': False})
    return jsonify({'response': False})


@app.route('/logout')
@login_required
def logout():
    user = Users.query.filter_by(email=current_user.email).first()
    logout_user()
    session['logged_in'] = False
    return render_template("homepage.html", name="homepage", session=session)


@app.route('/profile')
@login_required
def profile():
    return render_template('user_profile.html')


if __name__ == "__main__":
    db.create_all()
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000,
                        type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    app.run(debug=True, threaded=True)
