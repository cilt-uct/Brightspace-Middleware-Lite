# ruff: noqa: E402, I001
import json
from functools import wraps

from flask import request, Response

from project.app import alchemy_db
from .db.models import CallLog

def process_call_request(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        form_data = None
        file_data = None
        json_content = None
        raw_body = None

        # Capture headers and query args
        headers = dict(request.headers)
        args_dict = request.args.to_dict(flat=False)

        # Try to parse JSON safely and capture raw body for debugging
        if request.is_json:
            json_content = request.get_json(silent=True)
            raw_body = request.get_data(as_text=True)
        else:
            raw_body = request.get_data(as_text=True)

        if request.form:
            form_data = request.form.to_dict(flat=False)

        if request.files:
            file_data = {}
            for key, file in request.files.items():
                size = None
                preview = None
                stream = getattr(file, 'stream', None)

                # Try to get a content length without consuming the stream
                try:
                    size = file.content_length
                except Exception:
                    size = None

                # Safely read a small preview and restore stream position when possible
                if stream is not None:
                    try:
                        pos = stream.tell()
                    except Exception:
                        pos = None
                    try:
                        chunk = stream.read(1024)
                        if pos is not None:
                            stream.seek(pos)
                        try:
                            preview = chunk.decode('utf-8', errors='replace')
                        except Exception:
                            preview = str(chunk)
                        if size is None:
                            try:
                                cur = stream.tell()
                                stream.seek(0, 2)
                                size = stream.tell()
                                stream.seek(cur)
                            except Exception:
                                size = size
                    except Exception:
                        preview = None

                file_data[key] = {
                    'filename': getattr(file, 'filename', None),
                    'content_type': getattr(file, 'content_type', None),
                    'size': size,
                    'preview': preview,
                }

        request_body = {
            'url': request.url,
            'method': request.method,
            'headers': headers,
            'args': args_dict,
            'body': {'json': json_content, 'form': form_data, 'files': file_data, 'raw': raw_body},
        }

        # Do the request and on exception log the error
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            # log error case
            alchemy_db.session.add(
                CallLog(request=json.dumps(request_body), result=json.dumps({'error': str(e)}), status=500)
            )
            alchemy_db.session.commit()
            raise

        # Normalize response into JSON-serializable structure
        def _make_serializable(obj):
            if isinstance(obj, (dict, list, str, int, float, bool)) or obj is None:
                return obj
            if isinstance(obj, bytes):
                return obj.decode('utf-8', errors='replace')
            try:
                if isinstance(obj, str):
                    return json.loads(obj)
            except Exception:
                pass
            return str(obj)

        response_data = None
        status = 200

        if isinstance(result, tuple):
            body = result[0]
            # status may be the second element
            if len(result) > 1 and isinstance(result[1], int):
                status = result[1]
            # headers may be passed as second/third but we don't need them for logging here

            if isinstance(body, Response):
                response_data = body.get_json(silent=True)
                if response_data is None:
                    response_data = body.get_data(as_text=True)
                status = body.status_code
            else:
                response_data = body

        elif isinstance(result, Response):
            status = result.status_code
            response_data = result.get_json(silent=True)
            if response_data is None:
                response_data = result.get_data(as_text=True)
        else:
            response_data = result

        serializable_response = _make_serializable(response_data)

        # Truncate large 'data' fields to avoid storing huge payloads
        if isinstance(serializable_response, dict) and 'data' in serializable_response:
            v = serializable_response['data']
            if isinstance(v, list) and len(v) > 20:
                serializable_response['data'] = v[:20]
            elif isinstance(v, str) and len(v) > 1000:
                serializable_response['data'] = serializable_response['data'][:1000] + '...'

        # Persist call log (with fallback on serialization error)
        try:
            alchemy_db.session.add(
                CallLog(request=json.dumps(request_body),
                        result=json.dumps(serializable_response),
                        status=status)
            )
            alchemy_db.session.commit()
        except Exception:
            alchemy_db.session.rollback()
            alchemy_db.session.add(
                CallLog(request=json.dumps(request_body),
                        result=json.dumps({'result': str(serializable_response)}),
                        status=status)
            )
            alchemy_db.session.commit()

        return result

    return decorated_function
