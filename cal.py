import couchdbkit
import time
import datetime
import icalendar as ical
from flask import Flask
app = Flask(__name__)

@app.route("/")
def generate_calendar():
    c = ical.Calendar()

    db = couchdbkit.Server("http://habitat.habhub.org")['habitat']
    t = int(time.time())
    flights = db.view("calendar/flights", startkey=t, stale='update_after')

    for row in flights:
        e = ical.Event()
        e.add('summary', row['value']['name'] + " Launch")
        e.add('dtstart',
              datetime.datetime.fromtimestamp(row['value']['launch']['time']))
        e.add('dtend',
              datetime.datetime.fromtimestamp(row['value']['launch']['time']))
        e.add('dtstamp', datetime.datetime.utcnow())
        e['uid'] = row['id']
        c.add_component(e)

    return c.as_string()

if __name__ == "__main__":
    app.run()
