from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
  return "<h1>Hello! Ye website mobile se host hui hai!</h1>"


if __name__ == "__main__":
  app.r
  un()
