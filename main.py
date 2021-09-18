from flask import Flask

app = Flask(__name__)


@app.route('/')
def root():
    return "<p>Congrats!</p>"


if __name__ == '__main__':
    app.run(debug=True, port=8004)

