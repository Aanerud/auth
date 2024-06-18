import os
from flask import Flask, redirect, url_for, request, session
from flask_session import Session
import msal

app = Flask(__name__)
app.config['{RANDOM-KEY}'] = 'a random secret key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

client_id = '{CLIENT_ID}'
client_secret = '{CLIENT_SECRET}'
authority = 'https://login.microsoftonline.com/{TENANT_ID}'
redirect_uri = 'https://{AzureWebApp_Name}.azurewebsites.net/getAToken'
scope = ["User.Read"]

@app.route('/')
def index():
    session["flow"] = _build_auth_code_flow()
    return redirect(session["flow"]["auth_uri"])

@app.route('/getAToken')
def authorized():
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(session.get("flow", {}), request.args)
        if "error" in result:
            return f"Login failure: {result.get('error_description')}"
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
        return "Authentication successful for user: {}".format(session["user"]["name"])
    except ValueError as e:
        return f"Authentication failed: {e}"

def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        client_id, authority=authority,
        client_credential=client_secret, token_cache=cache)

def _build_auth_code_flow():
    return _build_msal_app().initiate_auth_code_flow(scope, redirect_uri=redirect_uri)

def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get('token_cache'):
        cache.deserialize(session['token_cache'])
    return cache

def _save_cache(cache):
    if cache.has_state_changed:
        session['token_cache'] = cache.serialize()

# The following block is for running the application locally.
# Azure Web App will pick up the `app` variable without needing this block.
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)