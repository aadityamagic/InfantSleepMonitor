from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://project:123456@localhost/appdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable Flask-SQLAlchemy modification tracking

# Create an instance of the SQLAlchemy class
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


@app.route('/')
@app.route('/home')
def home():
    return render_template('homepage.html', the_title='Home')


@app.route('/login.html')
def index():
    return render_template('login.html', the_title='Login')


@app.route('/login', methods=['POST'])
def login():
    # Check if the login is valid (you would typically do more here)
    if request.method == 'POST':
        # Perform login validation here
        # For simplicity, let's assume it's always valid
        return redirect(url_for('home'))


@app.route('/signup')
def signup():
    return render_template('signup.html', the_title='Signup')




@app.route('/analytics')
def analytics():
    return render_template('analytics.html', the_title='Analytics')


@app.route('/about')
def about():
    return render_template('about.html', the_title='About')


if __name__ == '__main__':
    app.run(debug=True)
