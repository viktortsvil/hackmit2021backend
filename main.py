from flask import Flask, request, Response
from notion_database.database import Database
from notion_database.properties import Properties, Children
from notion_database.page import Page
import time
import json
import hackmit.helper.errors as errors
import hackmit.helper.validators as validators
import hackmit.config as c
import requests
import lzstring
from random import sample
from pprint import pprint

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

    validated, response = validators.request_validator(request, validate)
    if not validated:
        return response

    try:
        ### PLACEHOLDER FOR GENERATING QUIZ

        ### PLACEHOLDER FOR PUTTING QUIZ LINK ON STUDENT PAGES
        return Response(json.dumps(errors.SUCCESS200), content_type="application/json"), 200
    except:
        return Response(json.dumps(errors.ERROR500), content_type="application/json"), 500


@app.route('/generate_sandbox', methods=['POST'])
def generate_sandbox():
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

    validated, response = validators.request_validator(request, validate)
    if not validated:
        return response

    try:
        ### PLACEHOLDER
        return Response(json.dumps(errors.SUCCESS200), content_type="application/json"), 200
    except:
        return Response(json.dumps(errors.ERROR500), content_type="application/json"), 500


def create_txt(tasks):
    result = ""
    for element in tasks:
        result += (element + "\n")

    x = lzstring.LZString()
    compressed = x.compressToEncodedURIComponent(json.dumps({
        "files": {
            "main.py": {
                "content": result,
                "isBinary": False
            },
            "package.json": {
                "content": {
                    "dependencies": {}
                }
            }
        }
    }))
    print(json.dumps({
        "files": {
            "main.py": {
                "content": result,
                "isBinary": False
            },
            "package.json": {
                "content": {
                    "dependencies": {}
                }
            }
        }
    }))
    r = requests.post(f'https://codesandbox.io/api/v1/sandboxes/define?parameters={compressed}')
    print(r.text.split('"@type":"SoftwareApplication')[0])
    return str(r.text.split('"@type":"SoftwareApplication')[0].split('"')[-2])


@app.route('/generate_tasks', methods=['POST'])
def generate_tasks():
    def validate(json_array):
        if not isinstance(json_array.get('quiz_id', None), str):
            return False
        return True

    validated, response = validators.request_validator(request, validate)
    if not validated:
        return response

    json_data = request.get_json()

    ### data extraction
    D = Database(integrations_token=c.token)
    D.find_all_page(database_id=c.scorelog_ID)
    P = Page(integrations_token=c.token)

    ### data filering
    relevant_students_to_topic = dict()
    topic_names = set()
    class_id = None
    for page in D.result['results']:
        if page['properties']['quiz_id']['select']['name'] == json_data['quiz_id']:
            student_name = page['properties']['student_id']['select']['name']
            if relevant_students_to_topic.get(student_name, None) is None:
                relevant_students_to_topic[student_name] = dict()
            topic_name = page['properties']['topic']['select']['name']
            topic_score = page['properties']['score']['number']
            relevant_students_to_topic[student_name][topic_name] = topic_score
            relevant_students_to_topic[student_name]['paired'] = None
            topic_names.add(topic_name)

            class_id = page['properties']['class_id']['select']['name']

    ### data restructurization
    relevant_students_to_topic = list(relevant_students_to_topic.items())
    for i in range(len(relevant_students_to_topic)):
        tmp = {"name": relevant_students_to_topic[i][0]}
        tmp.update(relevant_students_to_topic[i][1])
        relevant_students_to_topic[i] = tmp.copy()

    ### Matching algorithm
    KEY_KWD = ('name', 'paired', 'olss')
    for i in range(len(relevant_students_to_topic) - 1):
        best_match_student = None
        best_match_score = float('inf')
        student1 = relevant_students_to_topic[i]
        if isinstance(student1['paired'], str):
            continue
        for j in range(i + 1, len(relevant_students_to_topic)):
            student2 = relevant_students_to_topic[j]
            if isinstance(student2['paired'], str):
                continue
            olss = 0
            for key1 in student1.keys():
                if key1 not in KEY_KWD:
                    olss += (student2[key1] - student1[key1]) ** 2
            if olss <= best_match_score:
                best_match_score = olss
                best_match_student = student2
        student1['paired'] = best_match_student['name']
        best_match_student['paired'] = student1['name']

    ### get relevant topics list
    relevant_topics_list = set()
    for key1 in student1.keys():
        if key1 not in KEY_KWD:
            relevant_topics_list.add(key1)
    relevant_topics_list = list(relevant_topics_list)

    ### task db extraction
    relevant_tasks = {topic: [] for topic in relevant_topics_list}
    D.find_all_page(database_id=c.tasks_ID)
    for page in D.result['results']:
        topic_objects_list = page['properties']['task_topics']['multi_select']
        for topic_object in topic_objects_list:
            if topic_object['name'] in relevant_topics_list:
                relevant_tasks[topic_object['name']].append(page['properties']['task_id']['title'][0]['plain_text'])

    ### Writing into the database
    TASKS_PER_TOPIC = 1
    D.retrieve_database(c.todolist_ID)
    for student in relevant_students_to_topic:
        relevant_topics_local = set()
        if student['paired'] != '__finished':
            for topic, score in student.items():
                if topic not in KEY_KWD:
                    if score != 1:
                        relevant_topics_local.add(topic)
            ### TODO Optional: ADD TASK SELECTION FOR THE OTHER STUDENT IF PAIRED
            relevant_topics_local = list(relevant_topics_local)
            task_list = []
            for topic in relevant_topics_local:
                task_list += sample(relevant_tasks[topic], 1)

            PROPERTY = Properties()
            PROPERTY.set_title("todo_id", f"todo_3")
            PROPERTY.set_select("class_id", class_id)
            PROPERTY.set_multi_select("student_id", [student['name']])
            PROPERTY.set_number("task_timestamp", int(time.time()))
            # PROPERTY.set_url("task", link)  ### LINK!!!
            PROPERTY.set_multi_select("collaborators",
                                      [student['name']] + (
                                          [student['paired']] if student['paired'] is not None else []))
            # print(PROPERTY.result)
            # P.create_page(database_id=c.todolist_ID, properties=PROPERTY)

    return Response(json.dumps(relevant_students_to_topic), content_type="application/json"), 200


@app.route('/get_all_classes')
def get_all_classes():
    D = Database(integrations_token=c.token)
    D.find_all_page(database_id=c.classes_ID)
    # pprint(D.result['results'])

    lst = []
    for res in D.result['results']:
        _dict = {
            "class_topics": [],
            "class_foundational_topics": []
        }
        _dict["class_id"] = res['properties']['class_id']['title'][0]['text']['content']
        _dict["Class Name"] = res['properties']["Class Name"]['rich_text'][0]['text']['content']
        for topic in res['properties']['class_topics']['multi_select']:
            _dict['class_topics'].append(topic['name'])
        _dict['course_name'] = res['properties']['course_name']['select']['name']

        for ftopic in res['properties']['class_foundational_topics']['multi_select']:
            _dict['class_foundational_topics'].append(ftopic['name'])
            lst.append(_dict)

    return Response(json.dumps(lst), content_type="application/json",
                    headers=[('Access-Control-Allow-Origin', '*')]), 200


# get a list with the foundational topics of a class based on class id
def getClassTopics(class_id):
    headers = {
        "Authorization": "Bearer " + c.token,
        "Notion-Version": "2021-08-16",
        "Content-Type": "application/json"
    }
    readUrl = f"https://api.notion.com/v1/databases/{c.classes_ID}/query"
    res = requests.request("POST", readUrl, headers=headers)
    res = json.loads(res.text)

    class_topics = []
    for i in range(len(res['results'])):
        exit = 0
        if res['results'][i]['properties']['class_id']['title'][0]['text']['content'] == class_id:
            exit = 1
            for j in range(len(res['results'][i]['properties']['class_foundational_topics']['multi_select'])):
                class_topics.append(
                    res['results'][i]['properties']['class_foundational_topics']['multi_select'][j]['name'])
        if exit == 1:
            break

    return class_topics


# get a list with the quiz question ids based on the class id and questions/topic

def getTasksList(class_id, questions_per_topic):
    headers = {
        "Authorization": "Bearer " + c.token,
        "Notion-Version": "2021-08-16",
        "Content-Type": "application/json"
    }

    readUrl = f"https://api.notion.com/v1/databases/{c.quizquestions_ID}/query"
    res = requests.request("POST", readUrl, headers=headers)
    res = json.loads(res.text)
    class_topics = getClassTopics(class_id)
    questions = []

    for i in range(len(class_topics)):
        all_tasks = []
        for j in range(len(res['results'])):
            if res['results'][j]['properties']['quiz_question_topics']['select']['name'] == class_topics[i]:
                all_tasks.append(res['results'][j]['properties']['quiz_question_id']['title'][0]['text']['content'])
        if questions_per_topic > len(all_tasks):
            all_tasks = sample(all_tasks, len(all_tasks))
        else:
            all_tasks = sample(all_tasks, questions_per_topic)
        questions.extend(all_tasks)
    return (questions)


# create a row in the Quiz Archive database with the list of the quiz question ids
@app.route('/create_quiz', methods=['POST'])
def addQuizRow():
    def validate(json_array):
        if not isinstance(json_array.get('class_id', None), str):
            return False
        if not isinstance(json_array.get('questions_per_topic', None), int):
            return False
        return True

    validated, response = validators.request_validator(request, validate)
    if not validated:
        return response

    class_id = request.get_json()['class_id']
    questions_per_topic = request.get_json()['questions_per_topic']

    headers = {
        "Authorization": "Bearer " + c.token,
        "Notion-Version": "2021-08-16",
        "Content-Type": "application/json"
    }
    tasks_list = (getTasksList(class_id, questions_per_topic))

    createUrl = 'https://api.notion.com/v1/pages'
    UNIQUE_QUIZ_ID = str(int(time.time()))
    newPageData = {
        "parent": {"database_id": c.quizarchive_ID},
        "properties": {
            "quiz_id": {
                "title": [
                    {
                        "text": {
                            "content": UNIQUE_QUIZ_ID
                        }
                    }
                ]
            },
            "quiz_timestamp": {
                "number": int(time.time())
            },
            "class_id": {
                "select":
                    {
                        "name": class_id
                    }
            },
            "quiz_questions": {
                "multi_select": [{"name": task} for task in tasks_list]
            }
        }
    }

    data = json.dumps(newPageData)
    # print(str(uploadData))

    res = requests.request("POST", createUrl, headers=headers, data=data)

    D = Database(integrations_token=c.token)
    D.find_all_page(database_id=c.classes_ID)
    course_name = ""
    for page in D.result['results']:
        if (page['properties']['class_id']['title'][0]['plain_text']) == class_id:
            course_name = (page['properties']['course_name']['select']['name'])
    D.find_all_page(database_id=c.students_ID)
    relevant_students = []
    for student in D.result['results']:
        course_attending = student['properties']['courses_attending']['multi_select'][0]['name']
        if course_attending == course_name:
            relevant_students.append(student['properties']['student_id']['title'][0]['plain_text'])

    P = Page(integrations_token=c.token)
    for student in relevant_students:
        PROPERTY = Properties()
        PROPERTY.set_title("todo_id", f"{int(time.time())}")
        PROPERTY.set_select("class_id", class_id)
        PROPERTY.set_multi_select("student_id", [student])
        PROPERTY.set_number("task_timestamp", int(time.time()))
        PROPERTY.set_url("task",
                         f"https://georgiestonia.github.io/MiTeaFront/quiz.html?quizid={UNIQUE_QUIZ_ID}&studentid={student}")
        PROPERTY.set_multi_select("collaborators", [student])
        P.create_page(database_id=c.todolist_ID, properties=PROPERTY)

    return Response(json.dumps(errors.SUCCESS200), content_type="application/json",
                    headers=[('Access-Control-Allow-Origin', '*'),
                             ('Access-Control-Request-Method', 'POST'),
                             ('Access-Control-Request-Headers', 'X-PINGOTHER, Content-Type')]
                    ), 200


if __name__ == '__main__':
    app.run(debug=True, port=8004)
