from flask import Flask, request
from os import getenv, path
from json import loads as json_load
from subprocess import call
from config import *

CURDIR = path.dirname(path.abspath(__file__))

app = Flask(__name__)


@app.route('/')
def hello():
    return "Hello World!"


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

    branch = data.get('ref', '').partition('refs/heads/')[2].strip() or '<unknown branch>'

    return repo_url, repo_name, commit_id, branch


@app.route('/build', methods=['POST'])
def build():
    # extract data from body
    repo_url, repo_name, commit_id, branch = parse_request(request.data)
    # mode can be determined with get parameter, e.g "/build?m=bdist"
    mode = request.args.get('m', 'sdist')
    mode = mode if mode in ['sdist', 'bdist'] else 'sdist'

    if branch != "master":
        return "Ok. Nothing to build."

    app.logger.info('Starting to build '+repo_name+'...')

    # run the script build.sh
    return_code = call([path.join(CURDIR, 'build.sh'), repo_url,
                        repo_name, commit_id, branch, mode, DESTDIR])
    if return_code:
        app.logger.error("Build of "+repo_name+",  failed.")
        return "Error while building", 500

    app.logger.info('Done with '+repo_name+".")

    return "Ok"


if __name__ == "__main__":
    debug = getenv('FLASK_DEBUG', False)
    app.run(debug=debug, host='0.0.0.0')
