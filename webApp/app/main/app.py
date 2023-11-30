import csv
import json
import zipfile
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file, send_from_directory
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
app.config['MAIL_USERNAME'] = 'sleepmonitorwebapp@gmail.com'
app.config['MAIL_PASSWORD'] = 'sdxh djbq ctyi kkoe '#webapp@11 -->pw



mail = Mail(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    reset_token = db.Column(db.String(120), nullable=False)
    two_factor_code=None
    user_token=None
    path=None


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





@app.route('/login')
@app.route('/login', methods=['POST'])
def login():
    # Check if the login is valid (you would typically do more here)
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            User.two_factor_code = secrets.token_hex(3)  # Change the length as needed



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

@app.route('/')
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
    user = User.query.get(session['user_id'])
    # Specify the directory where your data files are stored
    data_directory = f'/home/aaditya/projectFiles/stage0/{user}'
    data1=data_directory
    if not os.path.exists(data_directory) or not os.path.isdir(data_directory):
        error_message = f"No Data found for user{user}"
        return render_template('analytics.html', error_message=error_message)

    # Get the list of files in the directory
    file_list = os.listdir(data_directory)

    # Separate files and folders
    files = []
    folders = []

    for item in file_list:
        full_path = os.path.join(data_directory, item)
        if os.path.isdir(full_path):
            folders.append(item)
        else:
            files.append(item)

    # Render the template with the lists of files and folders
    return render_template('view_data.html', files=files, folders=folders)

    # Render the template with the list of files
    return render_template('view_data.html', file_list=file_list)

@app.route('/export_data')
def export_data():
    user = User.query.get(session['user_id'])
    # Specify the directory where your data files are stored
    data_directory = f'/home/aaditya/projectFiles/stage3/{user}'
    if not os.path.exists(data_directory) or not os.path.isdir(data_directory):
        error_message = f"No Data found for user{user}"
        return render_template('analytics.html', error_message=error_message)

    # Get the list of files in the directory
    file_list = os.listdir(data_directory)

    # Separate files and folders
    files = []
    folders = []

    for item in file_list:
        full_path = os.path.join(data_directory, item)
        if os.path.isdir(full_path):
            folders.append(item)
        else:
            files.append(item)

    # Render the template with the lists of files and folders
    return render_template('export_data.html', files=files, folders=folders)

    # Render the template with the list of files
    return render_template('export_data.html', file_list=file_list)

def getDataDir():
    user = User.query.get(session['user_id'])
    # Specify the directory where your data files are stored
    return f'/home/aaditya/projectFiles/stage0/{user}'

def getpDataDir():
    user = User.query.get(session['user_id'])
    # Specify the directory where your data files are stored
    return f'/home/aaditya/projectFiles/stage3/{user}'
####################################################
@app.route('/download_file/<filename>')
def download_file(filename):
    user = User.query.get(session['user_id'])
    # Specify the directory where your data files are stored
    data_directory = f'/home/aaditya/projectFiles/stage0/{user}'
    return send_from_directory(data_directory, filename, as_attachment=True)

@app.route('/download_file_data/<filename>')
def download_file_data(filename):
    user = User.query.get(session['user_id'])
    # Specify the directory where your data files are stored
    data_directory = f'/home/aaditya/projectFiles/stage3/{user}'
    print("i ma here",data_directory)
    return send_from_directory(data_directory, filename, as_attachment=True)
# Route to handle opening folders
@app.route('/open_folder/<foldername>')
def open_folder(foldername):
    # Add logic to handle opening the folder
    # For example, you might list the contents of the folder
    # Replace this with your actual logic
    return f"Opening contents of folder: {foldername}"

@app.route('/open_folder_data/<foldername>')
def open_folder_data(foldername):
    # Add logic to handle opening the folder
    # For example, you might list the contents of the folder
    # Replace this with your actual logic
    return f"Opening contents of folder: {foldername}"

# Route to handle downloading the entire folder
@app.route('/download_folder/<foldername>')
def download_folder(foldername):
    folder_path = os.path.join(getDataDir(), foldername)

    # Check if the folder exists
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        flash(f"Folder {foldername} not found", 'error')
        return redirect(url_for('view_data'))

    # Create a ZIP file containing the folder's contents
    zip_filename = f"{foldername}_raw.zip"
    zip_path = os.path.join(getDataDir(), zip_filename)

    try:
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zip_file.write(file_path, arcname=arcname)

        # Return the ZIP file to the user for download
        return send_from_directory(getDataDir(), zip_filename, as_attachment=True)

    finally:
        # Remove the temporary ZIP file
        os.remove(zip_path)

@app.route('/download_folder_data/<foldername>')
def download_folder_data(foldername):
    print('=================',foldername,getpDataDir())
    folder_path = os.path.join(getpDataDir(), foldername)

    # Check if the folder exists
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        flash(f"Folder {foldername} not found", 'error')
        return redirect(url_for('view_data'))

    # Create a ZIP file containing the folder's contents
    zip_filename = f"{foldername}_processed.zip"
    zip_path = os.path.join(getpDataDir(), zip_filename)

    try:
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zip_file.write(file_path, arcname=arcname)

        # Return the ZIP file to the user for download
        return send_from_directory(getpDataDir(), zip_filename, as_attachment=True)

    finally:
        # Remove the temporary ZIP file
        os.remove(zip_path)
###################################################


@app.route('/about')
def about():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('about.html', the_title='About')
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))


@app.route('/plot')
def plot():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        flash('Run initiated check analytics', 'info')
        message = f'Run started by: {user} \n File location: {getDataDir()}'
        write_to_file(message, file_location=f'/home/aaditya/projectFiles/temp/{user}.json')
        data = read_csv_data(f'/home/aaditya/projectFiles/stage3/<User 13>/2023-11-22/test.csv')
        return render_template('plot.html', labels=data['labels'],values=data['values'])
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

def read_csv_data(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        data = {'labels': [], 'values': []}
        for row in reader:
            if row['timestamp'] and row['event']:
                data['labels'].append(row['timestamp'])
                data['values'].append(row['event'].replace("onset","0").replace("wakeup","1"))
    return data

def write_to_file(message, file_location):
    with open(file_location, 'a') as file:
        file.write(json.dumps(message) + '\n')

if __name__ == '__main__':
    app.run(debug=True)
