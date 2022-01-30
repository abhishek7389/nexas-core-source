import os
import base64
import json
import sqlalchemy
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email
from python_http_client.exceptions import HTTPError

connection_name = os.environ['CONNECTION']
table_name1 = "device"
table_name2 = "user"
db_name1 = "devices"
db_name2 = "users"
db_user = "root"
db_password = os.environ['DBPASS']

# If your database is MySQL, uncomment the following two lines:
driver_name = 'mysql+pymysql'
query_string = dict({"unix_socket": "/cloudsql/{}".format(connection_name)})

def nexas_alert_new(event, context):
    
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    print(pubsub_message)

    json_object1 = json.loads(pubsub_message)
    print("{}".format(json_object1["apikey"]))
    # If the type of your table_field value is a string, surround it with double quotes.
    stmt1 = sqlalchemy.text('SELECT * FROM {}.{} WHERE device_id = "{}"'.format(db_name1, table_name1, json_object1["device_id"]))
    stmt2 = sqlalchemy.text('SELECT username FROM {}.{} WHERE apikey = "{}"'.format(db_name2, table_name2, json_object1["apikey"]))
    stmt3 = sqlalchemy.text('SELECT email FROM {}.{} WHERE apikey = "{}"'.format(db_name2, table_name2, json_object1["apikey"]))
    
    db = sqlalchemy.create_engine(
      sqlalchemy.engine.url.URL(
        drivername=driver_name,
        username=db_user,
        password=db_password,
        query=query_string,
      ),
      pool_size=5,
      max_overflow=2,
      pool_timeout=30,
      pool_recycle=1800
    )
    try:
        with db.connect() as conn:
            q1 = conn.execute(stmt1)
            r1 = q1.fetchall()
            listToStr = ' '.join(map(str, r1))
            l1 = listToStr.replace(',)', ')')
            new1 = l1[ 1: -1]
            print(new1)
            q2 = conn.execute(stmt2)
            r2 = q2.fetchall()
            listToStr2 = ' '.join(map(str, r2))
            l2 = listToStr2.replace(',)', ')')
            new2 = str(l2[ 2: -2])
            print(new2)
            q3 = conn.execute(stmt3)
            r3 = q3.fetchall()
            listToStr3 = ' '.join(map(str, r3))
            l3 = listToStr3.replace(',)', ')')
            new3 = str(l3[ 2: -2])
            print(new3)
            log = logging.getLogger(__name__)

            SENDGRID_API_KEY = os.environ['SENDGRID_APIKEY_VAR']
            sg = SendGridAPIClient(SENDGRID_API_KEY)

            APP_NAME = "Nexas Core"
            name = "{}".format(new2)
            sensor_details = "{}".format(new1)
            client_mail_id = "{}".format(new3)

            html_content = f"""
            <p>Hello {name},</p>
            <br>
            <p>This mail is to notifiy you that your device is exceeded your alert condition</p>
            <br>
            <p>Device Details - </p>
            <br>
            <p>{sensor_details}</p>
            <br>
            <br>
            <br>
            <p>From,</p>
            <p>Nexas Core Support Team</p>
            """

            message = Mail(
                to_emails= client_mail_id,
                from_email=Email('g<SAMPLE_MAIL>', "Nexas Core Support"),
                subject=f"Alert Condition met on {APP_NAME}",
                html_content=html_content
                )
            message.add_bcc("sharmaabhishek7389@gmail.com")

            response = sg.send(message)
            print("Mail sent to {}".format(client_mail_id))

    
    except Exception as e:
        return 'Error: {}'.format(str(e))
    return 'ok'
