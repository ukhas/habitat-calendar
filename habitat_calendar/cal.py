import couchdbkit
import datetime
import icalendar
import pytz
from flask import Flask, Response
app = Flask(__name__)

def load_flights():
    db = couchdbkit.Server("http://beta.habitat.habhub.org")['habitat']
    view = db.view("flight/launch_time_including_payloads",
                   stale="update_after", include_docs=True)
    flights = []

    # very similar to habitat.uploader.Uploader.flights()
    for row in view:
        launch_timestamp, is_pcfg = row["key"]
        doc = row["doc"]

        if not is_pcfg:
            doc["_payload_docs"] = []
            doc["_launch_timestamp"] = launch_timestamp
            flights.append(doc)
        elif doc is not None:
            flights[-1]["_payload_docs"].append(doc)

    return flights

def launch_datetime(flight, add=0):
    # easier than importing utils.rfc3339
    timestamp = flight['_launch_timestamp'] + add
    timezone = pytz.timezone(flight['launch']['timezone'])
    utc_dt = pytz.utc.localize(datetime.datetime.utcfromtimestamp(timestamp))
    local_datetime = timezone.normalize(utc_dt.astimezone(timezone))

    return local_datetime

def flight_location(flight):
    location = flight['launch']['location']
    location_str = "lat: {latitude} lon: {longitude}".format(**location)
    if 'altitude' in location:
        location_str += " alt: {altitude}M".format(**location)

    location_name = flight.get('metadata', {}).get('location', None)
    if location_name is not None:
        location_str = u"{0} ({1})".format(location_name, location_str)

    return location_str

def describe_transmission(transmission):
    transmission = transmission.copy()
    transmission['freq_mhz'] = transmission['frequency'] / 1e6
    modulation = transmission['modulation']

    desc = u"{freq_mhz}MHz {mode} {modulation}"

    # copied from genpayload:
    if modulation == 'RTTY':
        if transmission['parity'] == 'none':
            transmission['parity'] = 'no'
        transmission['parity'] += ' parity'

        stop = transmission['stop']
        if stop == 1:
            stop = "1 stop bit"
        else:
            stop = "{0} stop bits".format(stop)
        transmission['stop'] = stop

        desc += " {baud} baud {shift}Hz shift {encoding} {parity} {stop}"
    elif modulation == 'DominoEX':
        desc += " {speed}"
    elif modulation == 'Hellschreiber':
        variant = transmission['variant']
        if variant == 'slowhell':
            transmission['modulation'] = "Slow Hell"
        else:
            transmission['modulation'] = "Feld Hell"

    return desc.format(**transmission)

def desc_from_payload(payload):
    # payload is a payload_configuration doc
    # produces: CALLSIGN1, C2, C3 on TRANSMISSION1, T2, T3

    callsigns = [s['callsign'] for s in payload.get('sentences', [])]

    transmissions = payload.get('transmissions', [])
    transmission_strs = map(describe_transmission, transmissions)

    description = u""

    if callsigns:
        description += ', '.join(callsigns)

    if callsigns and transmission_strs:
        description += " on "
        
    if transmission_strs:
        description += ', '.join(transmission_strs)

    return description

@app.route("/")
def calendar():
    cal = icalendar.Calendar()
    cal.add('prodid', '-//habhub//NONSGML habitat-calendar//EN')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'HAB launches')

    for flight in load_flights():
        desc = []

        metadata = flight.get('metadata', {}).copy()
        if 'location' in metadata:
            del metadata['location']

        if metadata:
            desc.append("Metadata:")
            for key, value in metadata.iteritems():
                desc.append(u"{key}: {value}".format(**locals()))

        if flight['_payload_docs']:
            if desc:
                desc.append("")
            desc.append("Payloads:")
            for doc in flight['_payload_docs']:
                description = desc_from_payload(doc)
                if description:
                    desc.append(description)

        e = icalendar.Event()
        e.add('summary', flight['name'])
        e.add('description', "\n".join(desc))
        e.add('location', flight_location(flight))
        e.add('dtstart', launch_datetime(flight))
        e.add('dtend', launch_datetime(flight, 4*3600))
        e.add('dtstamp', datetime.datetime.now(pytz.utc))
        e['uid'] = str(flight['_id'])
        cal.add_component(e)

    return Response(cal.to_ical(), mimetype='text/calendar')

if __name__ == "__main__":
    app.run()
