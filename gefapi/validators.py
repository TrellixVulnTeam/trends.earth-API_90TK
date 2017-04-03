"""GEFAPI VALIDATORS"""

import logging
import re

from functools import wraps
from flask import request, jsonify


EMAIL_REGEX = re.compile(r'^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$')


def error(status=400, detail='Bad Request'):
    return jsonify({
        'status': status,
        'detail': detail
    }), status


def validate_user_creation(func):
    """User Creation Validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        json_data = request.get_json()
        if 'email' not in json_data or 'password' not in json_data:
            return error(status=400, detail='Email and password are required')
        if not EMAIL_REGEX.match(json_data.get('email', None)):
            return error(status=400, detail='Email not valid')
        return func(*args, **kwargs)
    return wrapper


def validate_user_update(func):
    """User Update Validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        json_data = request.get_json()
        if 'password' not in json_data or 'role' not in json_data:
            return error(status=400, detail='Password or role are required')
        return func(*args, **kwargs)
    return wrapper


def validate_file(func):
    """Script File Validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'file' not in request.files:
            return error(status=400, detail='File Required')
        if request.files.get('file', None) is None:
            return error(status=400, detail='File Required')
        return func(*args, **kwargs)
    return wrapper