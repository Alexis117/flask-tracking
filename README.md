# Flask Tracking API

An API built with Python, Flask and GraphQL for register users and allow them to track their positions.

This API works together with an Expo - React Native App to share geolocation among users.

Run this app using gunicorn and the custom worker form gevent, otherwise websockets won`t work.

```
gunicorn -k "geventwebsocket.gunicorn.workers.GeventWebSocketWorker" wsgi:app
```
