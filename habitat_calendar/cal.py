import couchdbkit
import datetime
import icalendar
from flask import Flask, Response
app = Flask(__name__)

@app.route("/")
def calendar():
    cal = icalendar.Calendar()
    cal.add('prodid', '-//habhub//NONSGML habitat-calendar//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Upcoming HAB launches')

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
        cal.add_component(e)

    return Response(cal.to_ical(), mimetype='text/calendar')

if __name__ == "__main__":
    app.run()
