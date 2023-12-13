# wsgi.py

from test_controller import create_app

app = create_app()

if __name__ == "__main__":
    app.run()