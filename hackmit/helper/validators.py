from flask import Response
import json
import hackmit.helper.errors as errors

def request_validator(request, validate):
    if request.method.upper() != "POST":
        return False, (Response(json.dumps(errors.ERROR405), content_type="application/json"), 405)

    if request.headers.get("Content-Type", None) != "application/json":
        return False, (Response(json.dumps(errors.ERROR400), content_type="application/json"), 400)

    try:
        validated = True
        request_json = request.get_json()
    except:
        validated = False
        request_json = dict()
    if not validated or not validate(request_json):
        return False, (Response(json.dumps(errors.ERROR415), content_type="application/json"), 415)
    return True, (None, None)
