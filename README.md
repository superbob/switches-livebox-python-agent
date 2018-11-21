Switches Livebox Python Agent
=============================

This is an agent implementation compatible with https://github.com/superbob/switches-server.

It connects to a Livebox 4 which is a router provided by the French ISP _Orange_.

It authenticates against the switches server using a Google service account. See https://github.com/superbob/switches-server#technical-details for more details.

Install
-------

 1. Clone this repository on a Python 3 compatible system.
 2. (Optionally) Create a virtualenv.
 3. Check out requirements: `pip install -r requirements.txt`
 4. Copy the service account file containing credential information from the Google service account. The file has a name like _app-name-01234567890b.json_.
 5. Create a configuration file: Copy the `config.ini.example` file to `config.ini` and fill necessary information.
 6. (Optionally) Create a systemd unit file using the provided `switches-agent.service` file.

Google ID Token details
-----------------------

The [google_id_token.py](google_id_token.py) file contains all info related to Google ID Token authentication.

This file was greatly inspired by examples found on the following links:

 * https://cloud.google.com/endpoints/docs/openapi/service-account-authentication
 * https://developers.google.com/identity/protocols/OAuth2ServiceAccount

It can be run as a standalone program to obtain a Google ID Token from a service account file. Example:

```
./google_id_token.py app-name-01234567890b.json client-id.apps.googleusercontent.com
The following Google ID token has been generated
eyJhbGci...
```

This can be useful for debugging purposes.
