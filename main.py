from flask import Flask, render_template, request, make_response, redirect, url_for, flash, jsonify
import os
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, passwordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import datetime
import secrets
from avro.io import BinaryEncoder, DatumWriter
import avro
import io
import json
from google.cloud import pubsub_v1
from google.api_core.exceptions import NotFound
from google.cloud.pubsub import PublisherClient
from google.pubsub_v1.types import Encoding
from google.cloud import firestore

# Configuring your service account credentials 
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= "/home/abhisheksharma/Downloads/default-key.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]= "./nexas.json"

app = Flask(__name__)


# Google Cloud SQL variables for Setting up configuration
password ='akmwvd0HKcn218Dn'
#password = os.environ["PASSWORD"]
ip_address ='35.200.222.64'
#ip_address = os.environ["IP_ADDRESS"]
dbname ='users'
#dbname = os.environ["DBNAME"]
project_id ='halogen-ethos-275711'
#project_id = os.environ["PROJECT_ID"]
instance_name ='nexas-core' 
#instance_name = os.environ["INSTANCE_NAME"]

# Flask application configuration
app.config["SECRET_KEY"] = "mysecretkey"
app.config["SQLALCHEMY_DATABASE_URI"]= f"mysql+mysqldb://root:{password}@{ip_address}:3306/{dbname}?unix_socket=/cloudsql/halogen-ethos-275711:asia-south1:nexas-core"
app.config['SQLALCHEMY_BINDS']= {'sensors_data' : f"mysql+mysqldb://root:{password}@{ip_address}:3306/sensors_data?unix_socket=/cloudsql/halogen-ethos-275711:asia-south1:nexas-core",
                                  'devices' : f"mysql+mysqldb://root:{password}@{ip_address}:3306/devices?unix_socket=/cloudsql/halogen-ethos-275711:asia-south1:nexas-core"
                                }
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= True

#URI1= f"mysql+mysqldb://root:{password}@{ip_address}:3306/{dbname}?unix_socket=/cloudsql/halogen-ethos-275711:asia-south1:nexas-core"
#URI2= f"mysql+mysqldb://root:{password}@{ip_address}:3306/sensors_data?unix_socket=/cloudsql/halogen-ethos-275711:asia-south1:nexas-core"
#URI3= f"mysql+mysqldb://root:{password}@{ip_address}:3306/devices?unix_socket=/cloudsql/halogen-ethos-275711:asia-south1:nexas-core"

bootstrap = Bootstrap(app)

fdb = firestore.Client()

db = SQLAlchemy(app)
#db.create_engine(URI1, {})
#db.create_engine(URI2, {})
#db.create_engine(URI3, {})

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    apikey = db.Column(db.String(100), unique=True)
    LastUpdate = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    status = db.Column(db.String(10), default='ACTIVE')

class SensorData(db.Model):

    __bind_key__ = 'sensors_data'
    __tablename__ = 'SensorData'

    id = db.Column(db.Integer)
    sensor_type = db.Column(db.String(100))
    value_1 = db.Column(db.Integer)
    value_2 = db.Column(db.Integer)
    datetime_stamp = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    entryID = db.Column(db.Integer, primary_key = True)

class Sensor():
    id: int
    sensor_type: str
    value_1: int
    value_2: int

#api = 'abhishek'


#Creating model for database
class devices(db.Model):

    __bind_key__ = 'devices'
    __tablename__ = 'device'
    
    username = db.Column(db.String(15))
    entry_id = db.Column(db.Integer, primary_key = True)
    device_id = db.Column(db.Integer, unique=True)
    device_label = db.Column(db.String(100))
    sensor_type = db.Column(db.String(100))
    status = db.Column(db.String(20), default='ACTIVE')
    LastUpdate = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    alert_condition = db.Column(db.Integer)
 
 
    def __init__(self,username, device_id, device_label, sensor_type, status, LastUpdate, alert_condition):
         
        self.username = username
        self.device_id = device_id
        self.device_label = device_label
        self.sensor_type = sensor_type
        self.status = status
        self.LastUpdate = LastUpdate
        self.alert_condition = alert_condition
    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = passwordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = passwordField('password', validators=[InputRequired(), Length(min=8, max=80)])



@app.route('/')
def index():
    
    """new_data = SensorData(id=1, sensor_type='Gas Sensor', value_1=234, value_2=543)
    db.session.add(new_data)
    db.session.commit()"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            #if check_password_hash(user.password, form.password.data):
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('dashboard'))

        return '<h1>Invalid username or password</h1>'
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('login.html', form=form)



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        user_api = secrets.token_urlsafe(16)
        #hashed_password = form.password.data
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password, apikey=user_api)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('signup.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    all_data = SensorData.query.all()
    all_device = devices.query.filter_by(username=current_user.username)
    return render_template('dashboard.html', name=current_user.username, api_key=current_user.apikey, all_database_data = all_data, all_device_data = all_device)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/report')
@login_required
def report():
   all_data = SensorData.query.all()
   all_device = devices.query.filter_by(username=current_user.username)
   return render_template('report.html', name=current_user.username, api_key=current_user.apikey, all_database_data = all_data, all_device_data = all_device)

@app.route('/analytics')
@login_required
def analytics():
   all_data = SensorData.query.all()
   all_device = devices.query.filter_by(username=current_user.username)
   #new_ref = fdb.collection('data/userinfo/devices/sensor-device/thermal sensor')
   new_ref = fdb.collection('{}/{}/{}'.format(current_user.username, current_user.apikey, 2))
   #all_data = SensorData.query.all()
   docs = new_ref.stream()
   #all_device = devices.query.filter_by(username=current_user.username)
   return render_template('analytics.html', firestore_data = docs, name=current_user.username, api_key=current_user.apikey, all_database_data = all_data, all_device_data = all_device)

@app.route('/insert', methods = ['POST'])
def insert():

    if request.method == 'POST':

        username = current_user.username
        device_id = request.form['device_id']
        device_label = request.form['device_label']
        sensor_type = request.form['sensor_type']
        status = request.form['status']
        LastUpdate = datetime.datetime.utcnow()
        alert_condition = request.form['alert_condition']
# add cloud pubsub & cloud functions to perform the task
        new_device = devices(username, device_id, device_label, sensor_type, status, LastUpdate, alert_condition)
        db.session.add(new_device)
        db.session.commit()

        # if (conditon) to trigger the other cloud function to notify the user

        flash("New Data is added successfully.")

        return redirect(url_for('dashboard'))

@app.route('/update', methods = ['GET', 'POST'])
def update():
    
    if request.method == 'POST':
        new_device = devices.query.get(request.form.get('id'))
        
        #new_device.username = current_user.username
        new_device.device_id = request.form['device_id']
        new_device.device_label = request.form['device_label']
        #new_device.sensor_type = request.form['sensor_type']
        new_device.LastUpdate = datetime.datetime.utcnow()
        new_device.status = request.form['status']
        new_device.alert_condition = request.form['alert_condition']

        db.session.commit()
        flash("Sensor data Updated Successfully.")

        return redirect(url_for('dashboard'))

@app.route('/delete/<entry_id>/', methods = ['GET', 'POST'])
def delete(entry_id):
    new_device = devices.query.get(entry_id)
    db.session.delete(new_device)
    db.session.commit()
    flash("Sensor data deleted Successfully.")

    return redirect(url_for('dashboard'))

#@app.route('/post_data/<myusername>/<api_key>/<int:device_id>', methods = ['POST'])
@app.route('/post_data/', methods = ['POST'])
#def post_data(myusername=None, api_key=None, device_id=None): 
def post_data(): 

    headers = request.headers
    my_api_key = headers.get("X-Api-Key")
    my_device_id = headers.get("X-Device-Id")
    #only use api key
    details = User.query.filter_by(apikey=my_api_key).first()
    device_details = devices.query.filter_by(device_id=my_device_id).first()
    #checks - authorize api key, status of user active/not,
    
        #if details:
    #if details.status == "ACTIVE":
    #if api_key == details.apikey:
    if details.status == 'ACTIVE' and device_details != None:

    
        sensor = request.get_json(force=True)

        sensor.update(apikey = my_api_key) 
        sensor.update(device_id = my_device_id)


#header -> exract the key from the header & get details about the user 

        topic_path = 'projects/halogen-ethos-275711/topics/flask-test'

        publisher = pubsub_v1.PublisherClient()

        data = json.dumps(sensor).encode("utf-8")

        future = publisher.publish(topic_path, data)

        return 'The data is: {} \n'.format(data)
    else: 
        return {"Error": "Inserted API Key is not valied or you don't added device"} 


if __name__ == '__main__':
    app.run(debug=True)
