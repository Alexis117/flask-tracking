# Flask Geolocation Tracking API

GraphQL API built with Python using Flask for register users and allow them to track their positions.

This API works together with an Expo - React Native App to share geolocation among users.

## Usage

Run this app using gunicorn and the custom worker from gevent, otherwise websockets won`t work.

```
gunicorn -k "geventwebsocket.gunicorn.workers.GeventWebSocketWorker" wsgi:app
```

## Authentication over websockets

I enable websocket authentication through apollo client, so it takes a param called authToken at on connect event, so if you want to test it without apollo client you must be sure you send this token in your custom client. 

This is an example of apollo client:

```
const authLink = setContext(async (_, { headers }) => {
  const token = await AsyncStorage.getItem("userToken")
  console.log(token)
  return {
    headers: {
      ...Headers,
      Authorization: token ? token: ""  
      }
  }
});
```