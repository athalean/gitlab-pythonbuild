from flask import Flask, request
from os import getenv, path
from json import loads as json_load
from subprocess import call
from config import *
import re

TAG_REF_RE = re.compile(r'refs/tags/v(?P<version_string>.*?)$')

CURDIR = path.dirname(path.abspath(__file__))

app = Flask(__name__)


@app.route('/')
def hello():
    return "Please set up /build as a web hook in GitLab."


def parse_request(data):
    """
    Parses a GitLab web hook request.
    """
    data = json_load(data)
    try:
        # the clone url
        repo_url = data['repository']['url']
    except KeyError:
        return "Error: Could not extract repository URL", 400

    # the respoitory name
    repo_name = data['repository'].get('name', '<unknown repository>')

    try:
        # the id of the commit that we want to use to build
        commit_id = data['after']
    except KeyError:
        return "Error: invalid commit id"

    # by convention: Tags are named 'v1.2.3.4', setup script sets version number by environment variable
    tagref = TAG_REF_RE.match(data.get('ref', ''))

    version_string = ''

    if tagref and data.get('object_kind', '') == 'tag_push':
        version_string = tagref.group('version_string')

    return repo_url, repo_name, commit_id, version_string


@app.route('/build', methods=['POST'])
def build():
    # check the API key
    if request.args.get('key', '') != API_KEY:
        return "No valid key", 403

    # extract data from body
    repo_url, repo_name, commit_id, version_string = parse_request(request.data)
    # mode can be determined with get parameter, e.g "/build?m=bdist"
    mode = request.args.get('m', 'sdist')
    mode = mode if mode in ['sdist', 'bdist'] else 'sdist'

    if not version_string:
        return "Ok. Nothing to build."

    if path.isdir(path.join(CURDIR, 'tmp', repo_name+'_'+commit_id)):
        app.logger.error("Second build request ignored. Build is already running.")
        return "Still building..."

    app.logger.info('Starting to build '+repo_name+'...')

    # run the script build.sh
    return_code = call([path.join(CURDIR, 'build.sh'), repo_url,
                        repo_name, commit_id, version_string, mode, DESTDIR])
    if return_code:
        app.logger.error("Build of "+repo_name+",  failed.")
        return "Error while building", 500

    app.logger.info('Done with '+repo_name+".")

    return "Ok"


if __name__ == "__main__":
    debug = getenv('FLASK_DEBUG', False)
    app.run(debug=debug)
