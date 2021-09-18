from flask import Flask, request, make_response, Response
import json
import hackmit.helper.errors as errors

app = Flask(__name__)


@app.route('/')
def root():
    response = Response(json.dumps({"email": "v.tsvil@uni.minerva.edu"}), content_type="application/json")
    return response


@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    def validate(json_array):
        if not isinstance(json_array.get('class_id', None), int):
            return False
        if not isinstance(json_array.get('q_per_topic', None), int):
            return False
        return True

    if request.method.upper() != "POST":
        return Response(json.dumps(errors.ERROR405)), 405

    if request.headers.get("Content-Type", None) != "application/json":
        return Response(json.dumps(errors.ERROR400)), 400

    try:
        validated = True
        request_json = request.get_json()
    except:
        validated = False
        request_json = dict()
    if not validated or not validate(request_json):
        return Response(json.dumps(errors.ERROR415)), 415

    try:
        ### PLACEHOLDER FOR GENERATING QUIZ

        ### PLACEHOLDER FOR PUTTING QUIZ LINK ON STUDENT PAGES
        return Response(json.dumps(errors.SUCCESS200)), 200
    except:
        return Response(json.dumps(errors.ERROR500)), 500


@app.route('/generate_sandbox', methods=['POST'])
def generate_sandbox():
    """
    score_id: str
    student_id: str
    topic: str
    score: int
    timestamp: int
    class_id: str
    :return:
    """
    def validate(json_array):
        if not isinstance(json_array.get('score_id', None), str):
            return False
        if not isinstance(json_array.get('student_id', None), str):
            return False
        if not isinstance(json_array.get('topic', None), str):
            return False
        if not isinstance(json_array.get('score', None), int):
            return False
        if not isinstance(json_array.get('timestamp', None), int):
            return False
        if not isinstance(json_array.get('class_id', None), str):
            return False
        return True

    if request.method.upper() != "POST":
        return Response(json.dumps(errors.ERROR405)), 405

    if request.headers.get("Content-Type", None) != "application/json":
        return Response(json.dumps(errors.ERROR400)), 400

    try:
        validated = True
        request_json = request.get_json()
    except:
        validated = False
        request_json = dict()
    if not validated or not validate(request_json):
        return Response(json.dumps(errors.ERROR415)), 415

    try:
        ### PLACEHOLDER
        return Response(json.dumps(errors.SUCCESS200)), 200
    except:
        return Response(json.dumps(errors.ERROR500)), 500



if __name__ == '__main__':
    app.run(debug=True, port=8004)

#gunicorn3 --bind 127.0.0.1:8001 --log-file logs.txt --timeout 900 --daemon main:app
make_response()