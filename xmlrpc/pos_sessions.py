#!/usr/bin/env python2
#
# When a point of sale session is closed in backend without all the orders being
# sent from POS client (e.g. no internet), the orders are still linked to closed
# session, so no accounting entry is generated for them.
#
# What this script does:
# 1. open a new session (should not have running session), good idea to set a good name and dates
# 2. move all paid orders to the new session
# 3. user manually close the new pos session
# 4. correct the generated accounting entry to set correct date and period
#

from datetime import datetime
import xmlrpclib

# id of the point of sale config on which we will open the new sessions
POS_SESSION_ID = 1

host = 'localhost'
port = 8069
db = 'odoo-80'

# host = 'myinstance.odoo.com'
# port = '443'
# db = 'myinstance'

username = 'admin'
password = 'admin'

uid = None
url = '%s://%s:%s' % ('http' if port != 443 else 'https', host, port)  # for local instance
# url = '%s://%s' % ('http' if port != 443 else 'https', host)  # for saas instance

common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})
print "Logged in as %s (uid: %d)" % (username, uid)

models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

print "Generate new session"
new_session_id = models.execute_kw(db, uid, password, 'pos.session', 'create', [{
    'user_id': uid,
    'config_id': POS_SESSION_ID
}])

res = models.execute_kw(db, uid, password, 'pos.session', 'read', [[new_session_id], ['name']])
print "Current session: '%s'" % res[0]
new_name = raw_input("New name: ")
start_at = raw_input("New start date (e.g. '2015-04-01 06:30:00'): ")
stop_at = raw_input("New stop date: (e.g. '2015-04-01 17:30:00'): ")
res = models.execute_kw(db, uid, password, 'pos.session', 'write', [[new_session_id], {
    'name': new_name,
    'start_at': start_at,
}])

# new_session_id = 106
prev_session_id = input("Move orders from session?: ")
move = raw_input("Move orders to session %s? [y/N] " % new_session_id)
if move.lower() != 'y':
    import sys
    sys.exit()

res = models.execute_kw(db, uid, password, 'pos.order', 'search', [[('session_id', '=', prev_session_id), ('state', '=', 'paid')]])
print "Found %s orders" % len(res)
models.execute_kw(db, uid, password, 'pos.order', 'write', [res, {'session_id': new_session_id}])

raw_input("Press any key when the session is closed. ")
print "Updating closing date of %s at %s" % (new_session_id, stop_at)
res = models.execute_kw(db, uid, password, 'pos.session', 'write', [[new_session_id], {
    'stop_at': stop_at,
}])

stop_date = datetime.strptime(stop_at, "%Y-%m-%d %H:%M:%S").date().isoformat()
period_id = models.execute_kw(db, uid, password, 'account.period', 'find', [stop_date])[0]
print "Will update account.move to %s (period %s)" % (stop_date, period_id)

entry_id = input("ID of generated journal entry?: ")

models.execute_kw(db, uid, password, 'account.move', 'write', [[entry_id], {
    'date': stop_date,
    'period_id': period_id,
}])
