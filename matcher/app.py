import logging
import logging.handlers
import datetime
from matcher import app

#  This is the main app which is run by flask.  The Flask object is bound to app in the matcher package __init__.py
def app_init():

    # first get config settings for all matcher apps regardless of environment
    app.config.from_pyfile('../config.cfg')
    # now override using settings for this environment
    app.config.from_pyfile('../instance/config.cfg')
    fh = logging.handlers.RotatingFileHandler(filename=app.config['LOG_FILE'], mode='a', maxBytes=1*1000*1000, backupCount=20)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    # We always have a file for a log of errors.  In dev environment, also log to console
    if app.config['ENV'] == 'development':
        app.logger.addHandler(ch)
    app.logger.addHandler(fh)
    app.logger.debug("\n\n" + str(datetime.datetime.now()) + " Starting app")
    app.logger.debug("---------------------------------------------------------")


app_init()

