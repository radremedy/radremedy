
from flask import Flask, render_template
from models import db

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run()
