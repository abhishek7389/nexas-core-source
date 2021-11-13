import base64
import json
import os
import datetime
import sqlalchemy
from google.cloud import pubsub_v1
from google.cloud import firestore

connection_name = os.environ['CONNECTION']
#connection_name = "halogen-ethos-275711:asia-south1:nexas-core"
#table_name = os.environ['TABLE1']
table_name = "SensorData"
#table_name2 = os.environ['TABLE2']
table_name2 = "device"
#db_name = os.environ['DB1']
db_name = "sensors_data"
#db_name2 = os.environ['DB2']
db_name2 = "devices"
#db_user = os.environ['DBUSER']
db_user = "root"
db_password = os.environ['DBPASS']
#db_password = "akmwvd0HKcn218Dn"

db_name3 = "users" #os.environ['DB3'] #"users"
table_name3 = "user" #os.environ['TABLE3'] #"user"

#table_field = "id, sensor_type, value_1, value_2"


topic_path = 'projects/halogen-ethos-275711/topics/alert-mail'

# If your database is MySQL, uncomment the following two lines:
driver_name = 'mysql+pymysql'
query_string = dict({"unix_socket": "/cloudsql/{}".format(connection_name)})

#setting up firestore client
fdb = firestore.Client()

def nexas_ingestion(event, context):

    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    print(pubsub_message)

    json_object = json.loads(pubsub_message)
    #print('sensor type value is : "{}"'.format(json_object["sensor_type"]))
    # Uncomment and set the following variables depending on your specific instance and database:
    #table_field_value = (json_object["device_id"], json_object["sensor_type"] , json_object["value_1"], json_object["value_2"])  
    
    #stmt = sqlalchemy.text('insert into {} ({}) values {}'.format(table_name, table_field, table_field_value))
    stmt3 = sqlalchemy.text('SELECT username FROM {}.{} WHERE apikey = "{}"'.format(db_name3, table_name3, json_object["apikey"]))
    
    db = sqlalchemy.create_engine(
      sqlalchemy.engine.url.URL(
        drivername=driver_name,
        username=db_user,
        password=db_password,
        database=db_name,
        query=query_string,
      ),
      pool_size=5,
      max_overflow=2,
      pool_timeout=30,
      pool_recycle=1800
    )
    try:
        with db.connect() as conn:
                       #conn.execute(stmt)
            print("first query run successfully")
            q3 = conn.execute(stmt3)
            r3 = q3.fetchall()
            listToStr3 = ' '.join(map(str, r3))
            l3 = listToStr3.replace(',)', ')')
            new3 = (l3[ 2: -2])
            print(new3)
            curr = datetime.datetime.now().astimezone().isoformat()

            time1 = str(curr)
            print(time1)

            key1 = json_object["apikey"]
            device_id1 = json_object["device_id"]

            '''new_json = json_object'''

            if "apikey" in json_object:
              del json_object["apikey"]

            if "device_id" in json_object:
              del json_object["device_id"]

            print("worked  until this")
            
            #json_object134 = json.loads(new_json)

           # print(new_json)
           # print(new_json["value_1"])
            #print(json_object134)'''
            print(json_object)

            fdb.collection('{}/{}/{}'.format(new3, key1, device_id1)).document("{}".format(time1)).set(json_object)
            fdb.collection('{}/{}/{}'.format(new3, key1, device_id1)).document("{}".format(time1)).update({
                                                      u'timestamp': firestore.SERVER_TIMESTAMP
                                                    })
            print("Data is added into firestore")

            stmt1 = sqlalchemy.text('SELECT alert_condition FROM {}.{} WHERE (username = "{}" AND device_id = "{}")'.format(db_name2, table_name2, str(new3), device_id1))
    
            q1 = conn.execute(stmt1)
            print("this is working")
            alert_condition = q1.fetchall()
            listToStr = ' '.join(map(str, alert_condition))
            l1 = listToStr.replace(',)', ')')
            new1 = l1[ 1: -1]
            print(new1)
            print(alert_condition)
            for key in json_object:
              if (int(json_object[key]) >= int(new1)):
                  json_object.update(apikey=key1)
                  json_object.update(device_id=device_id1)
                  my_message = json_object
                  print(my_message)
                  publisher = pubsub_v1.PublisherClient()
                  data = json.dumps(my_message).encode("utf-8")
                  future = publisher.publish(topic_path, data)
                  print("Alert message is successfully sent to the user")
                  break
    except Exception as e:
        return 'Error: {}'.format(str(e))
    return 'ok'

    print("""This Function was triggered by messageId {} published at {} to {}
    """.format(context.event_id, context.timestamp, context.resource["name"]))
    
