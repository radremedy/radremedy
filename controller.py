
from flask import Flask
app = Flask(__name__)

@app.route("/hello/")
@app.route('/hello/<name>')
def hello():
     return render_template('index.html', name=name)

if __name__ == "__main__":
    app.run()
