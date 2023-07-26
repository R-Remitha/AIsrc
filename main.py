from app import app
from flask_navigation import Navigation

if __name__ == "__main__":
    app.debug = True
    app.run(debug=True, port=9999)
