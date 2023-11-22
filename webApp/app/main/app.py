from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from wtforms.validators import DataRequired, EqualTo
from wtforms import StringField, SubmitField, PasswordField
from flask_wtf import FlaskForm
import secrets,os,random,string


app = Flask(__name__)
app.secret_key = 'your_generated_secret_key'


#configuring database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://project:123456@localhost/appdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable Flask-SQLAlchemy modification tracking


# Create an instance of the SQLAlchemy class
db = SQLAlchemy(app)

#configuring mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'aaditya.a505@gmail.com'
app.config['MAIL_PASSWORD'] = 'tmdd zplu gcum raec '



mail = Mail(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    reset_token = db.Column(db.String(120), nullable=False)
    two_factor_code=None
    user_token=None


######################################password reset###################################3
class PasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

class PasswordResetConfirmForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm_Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

def send_reset_email(email, token, username):
    msg = Message('Password Reset Request', sender='aaditya.a505@gmail.com', recipients=[email])
    msg.body = f"Hi {username} /n Click the following link to reset your password: {url_for('reset_password', token=token, _external=True)}"
    mail.send(msg)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Check if the token is valid (you may want to implement token expiration logic)
    # If valid, allow the user to reset their password
    user = User.query.filter_by(reset_token=token).first()

    if token==User.reset_token:
        form = PasswordResetConfirmForm()




        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            user.password = hashed_password

            # Optionally, reset the password_reset_token here
            db.session.commit()

            flash('Your password has been reset successfully!', 'success')
            return redirect(url_for('login'))

        return render_template('reset_password.html', form=form, token=token)
    else:
        flash('Invalid or expired token. Please try again.', 'danger')
        return redirect(url_for('login'))

@app.route('/forgot_password')
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = PasswordResetForm()

    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        User.query.filter_by(email=email).first()



        # Check if the email is registered

        if user:
            # Generate a random token for password reset
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            # Save the token in your database or cache
            # In a real application, you'd probably want to associate the token with the user account
            User.reset_token=token
            db.session.commit()

            send_reset_email(email, token, user.username)
            flash('An email with instructions to reset your password has been sent.', 'info')
            return redirect(url_for('login'))

        flash('Email not found. Please register or enter a valid email.', 'danger')

    return render_template('forgot_password.html', form=form)

########################################################

@app.route("/signup", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')




@app.route('/')
@app.route('/login')
@app.route('/login', methods=['POST'])
def login():
    # Check if the login is valid (you would typically do more here)
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            User.two_factor_code = secrets.token_hex(5)  # Change the length as needed



            # Send the code via email
            send_two_factor_code(user.email, User.two_factor_code)

            # Log in the user and set the session variable
            session['user_id'] = user.id
            session['two_factor_authenticated'] = False
            flash('Login successful!', 'success')
            return redirect(url_for('auth'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
            error_message = 'Incorrect username or password. Please try again.'
            return render_template('login.html', error_message=error_message)
        # Perform login validation here
        # For simplicity, let's assume it's always valid
    return render_template('login.html')

def send_two_factor_code(email, code):

    msg = Message('Two-Factor Authentication Code', sender='aaditya.a505@gmail.com', recipients=[email])
    msg.body = f'Your two-factor authentication code is: {code}'
    mail.send(msg)


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if 'user_id' not in session or 'two_factor_authenticated' not in session:
        return redirect(url_for('login'))

    userid= session['user_id']


    if request.method == 'POST':

        entered_code = request.form.get('two_factor_code')



        if userid and entered_code == User.two_factor_code:
            # Mark the user as two-factor authenticated
            session['two_factor_authenticated'] = True
            return redirect(url_for('home'))
        else:
            error_message = 'Incorrect two-factor authentication code. Please try again.'
            return render_template('auth.html', error_message=error_message)

    return render_template('auth.html', error_message=None)
@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route("/profile")
def profile():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('profile.html', user=user)
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))


@app.route('/home')
def home():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('homepage.html', the_title='Home')
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))



@app.route('/analytics')
def analytics():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('analytics.html', the_title='Analytics')
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

        if request.method == 'POST':
            # Handle the uploaded file
            uploaded_file = request.files['file']

            if uploaded_file:
                # Save the file to a desired location
                date_today = datetime.now().strftime('%Y-%m-%d')
                upload_path = os.path.join('uploads', f'/home/aaditya/projectFiles/stage0/{user}/{date_today}/')
                os.makedirs(upload_path, exist_ok=True)
                uploaded_file = request.files['file']
                filename = secure_filename(uploaded_file.filename)
                file_path = os.path.join(upload_path, filename)
                uploaded_file.save(file_path)

                # You can perform additional processing with the uploaded file here

                return redirect(url_for('home'))
        return render_template('upload.html', the_title='Analytics')
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
@app.route('/view_data')
def view_data():
    # Specify the directory where your data files are stored
    data_directory = '/home/aaditya/projectFiles/'

    # Get the list of files in the directory
    file_list = os.listdir(data_directory)

    # Render the template with the list of files
    return render_template('view_data.html', file_list=file_list)

@app.route('/download_file/<filename>')
def download_file(filename):
    # Specify the directory where your data files are stored
    data_directory = '/home/aaditya/projectFiles/'

    # Generate the full path to the requested file
    file_path = os.path.join(data_directory, filename)

    # Use Flask's send_file to send the file for download
    return send_file(file_path, as_attachment=True)

@app.route('/about')
def about():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('about.html', the_title='About')
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)
