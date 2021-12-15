# fastapi-socketio-example
A simple fastapi app with socketio

# Get Started
```python
$ git clone https://github.com/millefalcon/fastapi-socketio-example
$ cd fastapi-socketio-example
$ python3 -m pip venv .env_dir
$ .env_dir/bin/activate
$ # for windows
$ # .env_dir\Scripts\activate
$ pip install -U pip wheel
$ pip install -r requirements.txt
$ export PORT=8000 # if windows, set the env variable as per spec.
$ uvicorn app:app --host 0.0.0.0 --port $PORT
```

Open `localhost:8000` in the browser, and you will be presented with a login screen.
For testing purpose, username's `johndoe` and `alice` are hardcoded.
One can login using either of those username and any non empty string as  password. *For the demo we are not validating password*


# TODO:
Add test
