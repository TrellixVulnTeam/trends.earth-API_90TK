
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import dateutil.parser
import logging

from flask import jsonify, request, send_from_directory, Response, json
from flask_jwt import jwt_required, current_identity

from gefapi.config import SETTINGS
from gefapi.routes.api.v1 import endpoints, error
from gefapi.validators import validate_user_creation, validate_user_update, \
    validate_file, validate_execution_update, validate_execution_log_creation, \
    validate_profile_update
from gefapi.services import UserService, ScriptService, ExecutionService
from gefapi.errors import UserNotFound, UserDuplicated, InvalidFile, ScriptNotFound, \
    ScriptDuplicated, NotAllowed, ExecutionNotFound, ScriptStateNotValid, EmailError


# SCRIPT CREATION
@endpoints.route('/script', strict_slashes=False, methods=['POST'])
@jwt_required()
@validate_file
def create_script():
    """
    Create a new script
    """
    logging.info('[ROUTER]: Creating a script')
    sent_file = request.files.get('file')
    if sent_file.filename == '':
        sent_file.filename = 'script'
    user = current_identity
    try:
        user = ScriptService.create_script(sent_file, user)
    except InvalidFile as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=400, detail=e.message)
    except ScriptDuplicated as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=400, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=user.serialize()), 200


@endpoints.route('/script', strict_slashes=False, methods=['GET'])
@jwt_required()
def get_scripts():
    """Get all scripts"""
    logging.info('[ROUTER]: Getting all scripts')
    include = request.args.get('include')
    include = include.split(',') if include else []
    try:
        scripts = ScriptService.get_scripts(current_identity)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=[script.serialize(include) for script in scripts]), 200


@endpoints.route('/script/<script>', strict_slashes=False, methods=['GET'])
@jwt_required()
def get_script(script):
    """Get a script"""
    logging.info('[ROUTER]: Getting script '+script)
    include = request.args.get('include')
    include = include.split(',') if include else []
    try:
        script = ScriptService.get_script(script, current_identity)
    except ScriptNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=script.serialize(include)), 200


@endpoints.route('/script/<script>/publish', strict_slashes=False, methods=['POST'])
@jwt_required()
def publish_script(script):
    """Publish a script"""
    logging.info('[ROUTER]: Publishsing script '+script)
    try:
        script = ScriptService.publish_script(script, current_identity)
    except ScriptNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=script.serialize()), 200


@endpoints.route('/script/<script>/unpublish', strict_slashes=False, methods=['POST'])
@jwt_required()
def unpublish_script(script):
    """Unpublish a script"""
    logging.info('[ROUTER]: Unpublishsing script '+script)
    try:
        script = ScriptService.unpublish_script(script, current_identity)
    except ScriptNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=script.serialize()), 200


@endpoints.route('/script/<script>/download', strict_slashes=False, methods=['GET'])
@jwt_required()
def download_script(script):
    """Download a script"""
    logging.info('[ROUTER]: Download script '+script)
    try:
        script = ScriptService.get_script(script, current_identity)
        return send_from_directory(directory=SETTINGS.get('SCRIPTS_FS'), filename=script.slug + '.tar.gz')
    except ScriptNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except NotAllowed as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=403, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')


@endpoints.route('/script/<script>/log', strict_slashes=False, methods=['GET'])
@jwt_required()
def get_script_logs(script):
    """Get a script logs"""
    logging.info('[ROUTER]: Getting script logs of script %s ' % (script))
    try:
        start = request.args.get('start', None)
        if start:
            start = dateutil.parser.parse(start)
        last_id = request.args.get('last-id', None)
        logs = ScriptService.get_script_logs(script, start, last_id)
    except ScriptNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=[log.serialize() for log in logs]), 200


@endpoints.route('/script/<script>', strict_slashes=False, methods=['PATCH'])
@jwt_required()
@validate_file
def update_script(script):
    """Update a script"""
    logging.info('[ROUTER]: Updating a script')
    sent_file = request.files.get('file')
    if sent_file.filename == '':
        sent_file.filename = 'script'
    user = current_identity
    if user.role != 'ADMIN' and user.email != 'gef@gef.com':
        return error(status=403, detail='Forbidden')
    try:
        script = ScriptService.update_script(script, sent_file, user)
    except InvalidFile as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=400, detail=e.message)
    except ScriptNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except NotAllowed as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=403, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=script.serialize()), 200


@endpoints.route('/script/<script>', strict_slashes=False, methods=['DELETE'])
@jwt_required()
def delete_script(script):
    """Delete a script"""
    logging.info('[ROUTER]: Deleting script: '+script)
    identity = current_identity
    if identity.role != 'ADMIN' and identity.email != 'gef@gef.com':
        return error(status=403, detail='Forbidden')
    try:
        script = ScriptService.delete_script(script, identity)
    except ScriptNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=script.serialize()), 200


# SCRIPT EXECUTION
@endpoints.route('/script/<script>/run', strict_slashes=False, methods=['POST'])
@jwt_required()
def run_script(script):
    """Run a script"""
    logging.info('[ROUTER]: Running script: '+script)
    user = current_identity
    try:
        params = request.args.to_dict() if request.args else {}
        if request.get_json(silent=True):
            params.update(request.get_json())
        if 'token' in params:
            del params['token']
        execution = ExecutionService.create_execution(script, params, user)
    except ScriptNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except ScriptStateNotValid as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=400, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=execution.serialize()), 200


@endpoints.route('/execution', strict_slashes=False, methods=['GET'])
@jwt_required()
def get_executions():
    """Get all executions"""
    logging.info('[ROUTER]: Getting all executions: ')
    include = request.args.get('include')
    include = include.split(',') if include else []
    try:
        executions = ExecutionService.get_executions(current_identity)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=[execution.serialize(include) for execution in executions]), 200


@endpoints.route('/execution/<execution>', strict_slashes=False, methods=['GET'])
@jwt_required()
def get_execution(execution):
    """Get an execution"""
    logging.info('[ROUTER]: Getting execution: '+execution)
    include = request.args.get('include')
    include = include.split(',') if include else []
    try:
        execution = ExecutionService.get_execution(execution, current_identity)
    except ExecutionNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=execution.serialize(include)), 200


@endpoints.route('/execution/<execution>', strict_slashes=False, methods=['PATCH'])
@jwt_required()
@validate_execution_update
def update_execution(execution):
    """Update an execution"""
    logging.info('[ROUTER]: Updating execution '+execution)
    body = request.get_json()
    user = current_identity
    if user.role != 'ADMIN' and user.email != 'gef@gef.com':
        return error(status=403, detail='Forbidden')
    try:
        execution = ExecutionService.update_execution(body, execution)
    except ExecutionNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=execution.serialize()), 200


@endpoints.route('/execution/<execution>/log', strict_slashes=False, methods=['GET'])
def get_execution_logs(execution):
    """Get the exectuion logs"""
    logging.info('[ROUTER]: Getting exectuion logs of execution %s ' % (execution))
    try:
        start = request.args.get('start', None)
        if start:
            start = dateutil.parser.parse(start)
        last_id = request.args.get('last-id', None)
        logs = ExecutionService.get_execution_logs(execution, start, last_id)
    except ExecutionNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=[log.serialize() for log in logs]), 200


@endpoints.route('/execution/<execution>/download-results', strict_slashes=False, methods=['GET'])
def get_download_results(execution):
    """Download results of the exectuion"""
    logging.info('[ROUTER]: Download execution results of execution %s ' % (execution))
    try:
        execution = ExecutionService.get_execution(execution)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')

    return Response(
        json.dumps(execution.results),
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=results.json"}
    )


@endpoints.route('/execution/<execution>/log', strict_slashes=False, methods=['POST'])
@jwt_required()
@validate_execution_log_creation
def create_execution_log(execution):
    """Create log of an execution"""
    logging.info('[ROUTER]: Creating execution log for '+execution)
    body = request.get_json()
    user = current_identity
    if user.role != 'ADMIN' and user.email != 'gef@gef.com':
        return error(status=403, detail='Forbidden')
    try:
        log = ExecutionService.create_execution_log(body, execution)
    except ExecutionNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=log.serialize()), 200


# USER
@endpoints.route('/user', strict_slashes=False, methods=['POST'])
@jwt_required()
@validate_user_creation
def create_user():
    """Create an user"""
    logging.info('[ROUTER]: Creating user')
    body = request.get_json()
    identity = current_identity
    user_role = body.get('role', 'USER')
    if identity.role == 'USER' and user_role == 'ADMIN':
        return error(status=403, detail='Forbidden')
    try:
        user = UserService.create_user(body)
    except UserDuplicated as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=400, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=user.serialize()), 200


@endpoints.route('/user', strict_slashes=False, methods=['GET'])
@jwt_required()
def get_users():
    """Get users"""
    logging.info('[ROUTER]: Getting all users')
    include = request.args.get('include')
    include = include.split(',') if include else []
    identity = current_identity
    if identity.role != 'ADMIN' and identity.email != 'gef@gef.com':
        return error(status=403, detail='Forbidden')
    try:
        users = UserService.get_users()
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=[user.serialize(include) for user in users]), 200


@endpoints.route('/user/<user>', strict_slashes=False, methods=['GET'])
@jwt_required()
def get_user(user):
    """Get an user"""
    logging.info('[ROUTER]: Getting user'+user)
    include = request.args.get('include')
    include = include.split(',') if include else []
    identity = current_identity
    if identity.role != 'ADMIN' and identity.email != 'gef@gef.com':
        return error(status=403, detail='Forbidden')
    try:
        user = UserService.get_user(user)
    except UserNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=user.serialize(include)), 200


@endpoints.route('/user/me', strict_slashes=False, methods=['GET'])
@jwt_required()
def get_me():
    """Get me"""
    logging.info('[ROUTER]: Getting my user')
    user = current_identity
    return jsonify(data=user.serialize()), 200


@endpoints.route('/user/me', strict_slashes=False, methods=['PATCH'])
@jwt_required()
@validate_profile_update
def update_profile():
    """Update an user"""
    logging.info('[ROUTER]: Updating profile profile')
    body = request.get_json()
    identity = current_identity
    try:
        user = UserService.update_profile_password(body, identity)
    except UserNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=user.serialize()), 200


@endpoints.route('/user/<user>/recover-password', strict_slashes=False, methods=['POST'])
def recover_password(user):
    """Revover password"""
    logging.info('[ROUTER]: Recovering password')
    try:
        user = UserService.recover_password(user)
    except UserNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except EmailError as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=user.serialize()), 200


@endpoints.route('/user/<user>', strict_slashes=False, methods=['PATCH'])
@jwt_required()
@validate_user_update
def update_user(user):
    """Update an user"""
    logging.info('[ROUTER]: Updating user'+user)
    body = request.get_json()
    identity = current_identity
    if identity.role != 'ADMIN' and identity.email != 'gef@gef.com':
        return error(status=403, detail='Forbidden')
    try:
        user = UserService.update_user(body, user)
    except UserNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=user.serialize()), 200


@endpoints.route('/user/<user>', strict_slashes=False, methods=['DELETE'])
@jwt_required()
def delete_user(user):
    """Delete an user"""
    logging.info('[ROUTER]: Deleting user'+user)
    identity = current_identity
    if user == 'gef@gef.com':
        return error(status=403, detail='Forbidden')
    if identity.role != 'ADMIN' and identity.email != 'gef@gef.com':
        return error(status=403, detail='Forbidden')
    try:
        user = UserService.delete_user(user)
    except UserNotFound as e:
        logging.error('[ROUTER]: '+e.message)
        return error(status=404, detail=e.message)
    except Exception as e:
        logging.error('[ROUTER]: '+str(e))
        return error(status=500, detail='Generic Error')
    return jsonify(data=user.serialize()), 200
