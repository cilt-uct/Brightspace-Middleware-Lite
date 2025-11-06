# Middleware to Brightspace Migration (Lite)

This service is to handle the communication between the [Migration Tsugi Tool](https://github.com/cilt-uct/tsugi-migrate-to-brightspace) and D2L Brightspace. It does this by wrapping a `CALL` function that the migration scripts use to communicate with LMS with the appropriate OAuth 2.0 token. It also manages the refreshing of said token.

## Structure

The serivce is split into a FastApi UI/API and a APSCheduler to manage the refreshing of the token.

***Note:*** **This service is still in development and testing and is not suitable for production.**


Install required packages:
```
pip install -r app/requirements.txt
```

Remove all installe packages:
```
pip freeze | xargs pip uninstall -y
```
