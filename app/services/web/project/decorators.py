import json

from flask import current_app, session, request, Response
from flask_login import current_user
from functools import wraps

from .db.models import CallLog
from project.app import alchemy_db

SERVICE_NOW_USERNAME = "servicenow_script"

def process_call_request(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        form_data = None
        file_data = None
        json_content = None

        # Check if the request is JSON, form data, or file upload
        if request.is_json:
            json_content = request.get_data(as_text=True)
        elif request.form:
            form_data = request.form.to_dict(flat=False)
        elif request.files:
            file_data = {
                key: {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size": len(file.read())
                }
                for key, file in request.files.items()
            }

        request_body = {
            'url': request.url,
            'method': request.method,
            'body': {'json': json_content, 'form': form_data, 'files': file_data}
        }

        # Do the request and on exception log the error
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            # log error case
            alchemy_db.session.add(CallLog(
                request=json.dumps(request_body),
                result=json.dumps({"error": str(e)}),
                status=500
            ))
            alchemy_db.session.commit()
            raise

        # Normalize response
        request_result = None
        status = 200
        if isinstance(result, tuple):

            if isinstance(result[0], Response):
                request_result = result[0].get_json() if hasattr(result[0], 'get_json') else result[0].data
                status = result[0].status_code
            else:
                request_result = result[0]
                status = result[1] if len(result) > 1 and isinstance(result[1], int) else 200

        elif isinstance(result, Response):
            try:
                request_result = result.get_json()
                status = result.status_code
            except Exception:
                request_result = {"status": result.status_code}
                status = result.status_code
        else:
            request_result = result

        if isinstance(request_result, dict) and 'data' in request_result and len(request_result['data']) > 20:
            request_result['data'] = request_result['data'][0:20]

        alchemy_db.session.add(CallLog(request=json.dumps(request_body),
                                             result=json.dumps(request_result),
                                             status=status))
        alchemy_db.session.commit()

        return result

    return decorated_function
