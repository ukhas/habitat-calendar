import couchdbkit
import datetime
import icalendar
import pytz
from flask import Flask, Response
app = Flask(__name__)

def desc_from_payload(payload, config):
    pairs = {}
    try:
        pairs.update(config['radio'])
        if type(config['telemetry']) == list:
            for telem in config['telemetry']:
                pairs.update(telem)
        else:
            pairs.update(config['telemetry'])
    except KeyError:
        pass
    
    return ("{0}: ".format(payload) + 
            ", ".join("{0}: {1}".format(k, v) for k, v in pairs.iteritems()))

@app.route("/")
def calendar():
    cal = icalendar.Calendar()
    cal.add('prodid', '-//habhub//NONSGML habitat-calendar//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'HAB launches')

    db = couchdbkit.Server("http://habitat.habhub.org")['habitat']
    flights = db.view("calendar/flights", stale='update_after')

    for flight in flights:
        launchtime = flight['key']
        desc = []
        if 'metadata' in flight['value']:
            desc.append("Metadata:")
            for key, value in flight['value']['metadata'].iteritems():
                desc.append("{key}: {value}".format(**locals()))
        if 'payloads' in flight['value']:
            desc.append("")
            desc.append("Payloads:")
            for payload, config in flight['value']['payloads'].iteritems():
                desc.append(desc_from_payload(payload, config))
        e = icalendar.Event()
        e.add('summary', flight['value']['name'] + " Launch")
        e.add('description', "\n".join(desc))
        e.add('dtstart', datetime.datetime.fromtimestamp(launchtime, pytz.utc))
        e.add('dtend', datetime.datetime.fromtimestamp(launchtime + 4*3600,
            pytz.utc))
        e.add('dtstamp', datetime.datetime.now(pytz.utc))
        e['uid'] = str(flight['id'])
        cal.add_component(e)

    return Response(cal.to_ical(), mimetype='text/calendar')

if __name__ == "__main__":
    app.run(debug=True)
