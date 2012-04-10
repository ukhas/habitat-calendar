import couchdbkit
import datetime
import icalendar
from flask import Flask, Response
app = Flask(__name__)

@app.route("/")
def calendar():
    c = icalendar.Calendar()
    db = couchdbkit.Server("http://habitat.habhub.org")['habitat']
    flights = db.view("calendar/flights", stale='update_after')

    for flight in flights:
        launchtime = flight['key']
        e = icalendar.Event()
        e.add('summary', flight['value']['name'] + " Launch")
        e.add('dtstart', datetime.datetime.fromtimestamp(launchtime))
        e.add('dtend', datetime.datetime.fromtimestamp(launchtime + 4*3600))
        e.add('dtstamp', datetime.datetime.utcnow())
        e['uid'] = flight['id']
        c.add_component(e)

    return Response(c.as_string(), mimetype='text/calendar')

if __name__ == "__main__":
    app.run()
