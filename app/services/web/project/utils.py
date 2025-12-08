# ruff: noqa: E402, I001
import base64
import ipaddress
import json
import mimetypes
import re
import zipfile
from datetime import datetime

from flask import current_app, jsonify

from .constants import ROLES, SAKAI_ROLES

class Utils:

    @staticmethod
    def format_time(value: datetime, is_webhook: bool = False) -> str:
        if is_webhook:
            return value.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return value.strftime('%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def get_json_from_base64(_str: str) -> dict:
        """Convert input from base64 encoding to JSON dict

        Args:
            _str (str): token string part

        Returns:
            dict: JSON dict
        """
        decoded_bytes = base64.b64decode(_str + '=' * (-len(_str) % 4))
        # decoded_str = decoded_bytes.decode('ascii')
        return json.loads(decoded_bytes)

    # Python code to merge dict using a single expression
    @staticmethod
    def dict_merge(dict1, dict2):
        res = {**dict1, **dict2}
        return res

    @staticmethod
    def get_id_from_valid_or_default(func, a, b) -> int:
        val = 0

        run_a = func(a)
        if run_a['status'] == 'success':
            val = run_a['data']['Identifier']
        else:
            run_b = func(b)
            if run_b['status'] == 'success':
                val = run_b['data']['Identifier']

        return int(val)

    @staticmethod
    def escape_name(s):
        """Escape name to avoid SQL injection and keyword clashes.
        Doubles embedded backticks, surrounds the whole in backticks.
        Note: not security hardened, caveat emptor.
        """
        return '`{}`'.format(s.replace('`', '``'))

    @staticmethod
    def allowed_file_zip(file):
        filename = file.filename
        if '.' not in filename:
            return False

        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in ['zip']:
            return False

        # Check actual file header by attempting to open as a ZIP
        try:
            file.stream.seek(0)  # Reset pointer
            with zipfile.ZipFile(file.stream) as z:
                test_result = z.testzip()
                file.stream.seek(0)  # Reset again for later use
                return test_result is None  # If None, the archive is good
        except Exception:
            return False

    @staticmethod
    def allowed_file_csv(file):
        filename = file.filename
        if '.' not in filename:
            return False

        ext = filename.rsplit('.', 1)[1].lower()
        if ext not in ['csv', 'xlsx']:
            return False

        # MIME type check
        mime_type = file.mimetype
        allowed_mime_types = {
            'csv': {'text/csv', 'application/csv'},
            'xlsx': {
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.ms-excel'
            }
        }

        return mime_type in allowed_mime_types.get(ext, set())

    @staticmethod
    def get_mime_type(ext:str):
        mime_type, _ = mimetypes.guess_type(f'file.{ext}')
        return mime_type

    @staticmethod
    def is_valid_email(email):
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(email_pattern, email) is not None

    @staticmethod
    def parse_request_data(request):
        content_type = request.headers.get('Content-Type','')

        if content_type.startswith('application/json'):
            return request.get_json()

        elif content_type.startswith('application/x-www-form-urlencoded'):
            return request.form.to_dict()

        elif content_type.startswith('multipart/form-data'):
            return request.form

        return None

    @staticmethod
    def batch(iterable, size: int) -> list:
        """Yield successive chunks of a given size from an iterable."""
        batch_list = []
        for item in iterable:
            batch_list.append(item)
            if len(batch_list) == size:
                yield batch_list
                batch_list = []
        if batch_list:
            yield batch_list

    # Append or increment a -D suffix to a string code to help track duplicates
    # (e.g., in course codes or IDs).
    @staticmethod
    def add_duplicate_postfix(code):
        match = re.search(r'(-D(\d+))$', code)
        if not match:
            if code.endswith('-D'):
                return f'{code}2'
            return f'{code}-D'

        prefix = code[: -len(match.group(1))]
        number = int(match.group(2)) + 1
        return f'{prefix}-D{number}'


    # Replaces a 4-digit year (like 2023) that is
    # preceded by - or _ with a new term value, while preserving the original separator (- or _).
    @staticmethod
    def replace_year(st, term):
        return re.sub(r'([-_])\d{4}(?![A-Z])', lambda match: f'{match.group(1)}{term}', st)

    @staticmethod
    def get_order_column_name(order, columns):
        order_column_index = order[0]['column']

        if 0 <= order_column_index < len(columns):
            order_column_name = columns[order_column_index]['data']
            return order_column_name, order[0]['dir']
        else:
            return None, 'asc'

    @staticmethod
    def organize_by_faculty(data):
        organized_data = {}
        for item in data:
            faculty = item['faculty_name']
            code = item['code']
            name = item['name']

            if faculty not in organized_data:
                organized_data[faculty] = []

            organized_data[faculty].append({'code': code, 'name': name})

        return organized_data

    @staticmethod
    def get_internal_role(_role: str | int) -> int:
        if isinstance(_role, int):
            return _role
        elif isinstance(_role, str):
            if _role in ROLES:
                return ROLES[_role]
        return 0

    @staticmethod
    def map_sakai_roles_to_internal(_role: str) -> int:
        if _role:
            if isinstance(_role, str) and _role.lower() in SAKAI_ROLES:
                return SAKAI_ROLES[_role.lower()]

        return 0

    @staticmethod
    def is_allowed(remote_ip):
        # Check if remote IP is in allowed hosts or CIDR ranges
        for host in current_app.config['CALL_ALLOWED_HOST']:
            if remote_ip == host:
                return True
            try:
                if ipaddress.ip_address(remote_ip) in ipaddress.ip_network(host, strict=False):
                    return True
            except ValueError:
                continue  # Not an IP or CIDR, just a hostname check
        return False

    @staticmethod
    def get_client_ip(request):
        # Get the IP from X-Forwarded-For if behind a proxy
        if 'X-Forwarded-For' in request.headers:
            ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
        else:
            ip = request.remote_addr  # Fallback if not behind a proxy
        return ip

    @staticmethod
    def return_success_state(msg, code: int = 200):
        return (jsonify({'status': 'success', 'data': msg}), code)

    @staticmethod
    def return_error_state(msg, code: int = 400):
        return (jsonify({'status': 'ERR', 'data': msg}), code)
