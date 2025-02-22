from dotenv import load_dotenv
import os
from nylas import Client
from flask import Flask, request, redirect, jsonify, session
from nylas.models.auth import URLForAuthenticationConfig
from nylas.models.auth import CodeExchangeRequest
from flask_cors import CORS

load_dotenv()

# Add this after load_dotenv()
required_env_vars = [
    "NYLAS_CLIENT_ID",
    "NYLAS_CALLBACK_URI",
    "NYLAS_API_KEY",
    "NYLAS_API_URI",
]

# Check if all required environment variables are set
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print("Error: Missing required environment variables:")
    for var in missing_vars:
        print(f"- {var}")
    print("\nPlease set these variables in your .env file")

nylas_config = {
    "client_id": os.getenv("NYLAS_CLIENT_ID"),
    "callback_uri": os.getenv("NYLAS_CALLBACK_URI"),
    "api_key": os.getenv("NYLAS_API_KEY"),
    "api_uri": os.getenv("NYLAS_API_URI"),
}

# Add error handling for Nylas client initialization
try:
    nylas = Client(
        api_key=nylas_config["api_key"],
        api_uri=nylas_config["api_uri"],
    )
except Exception as e:
    print(f"Error initializing Nylas client: {str(e)}")

app = Flask(__name__)
CORS(app)
# Add secret key for session management
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your-secret-key")

# Add a root route for testing
@app.route("/", methods=["GET"])
def index():
    return "Nylas OAuth Service is running!"

@app.route("/nylas/auth", methods=["GET"])
def nylas_auth():
    """
    Initiates the Nylas OAuth2 flow by redirecting to Nylas login
    """
    auth_url = nylas.auth.url_for_oauth2({
        "client_id": nylas_config["client_id"],
        "redirect_uri": nylas_config["callback_uri"],
    })
    return redirect(auth_url)

@app.route("/oauth/exchange", methods=["GET"])
def oauth_exchange():
    """
    Handles the OAuth2 callback from Nylas
    """
    code = request.args.get("code")

    if not code:
        return "No authorization code returned from Nylas", 400

    try:
        exchange_request = CodeExchangeRequest({
            "redirect_uri": nylas_config["callback_uri"],
            "code": code,
            "client_id": nylas_config["client_id"]
        })
        
        exchange = nylas.auth.exchange_code_for_token(exchange_request)
        grant_id = exchange.grant_id

        # Store the grant_id in session for later use
        session['grant_id'] = grant_id

        return jsonify({
            "message": f"OAuth2 flow completed successfully for grant ID: {grant_id}",
            "grant_id": grant_id
        })
    except Exception as e:
        return f"Failed to exchange authorization code for token: {str(e)}", 500

# Example route to test email access after authentication
@app.route("/nylas/recent-emails", methods=["GET"])
def recent_emails():
    """
    Retrieves recent emails using the stored grant_id
    """
    if 'grant_id' not in session:
        return "Not authenticated with Nylas", 401

    try:
        query_params = {"limit": 5}
        messages = nylas.messages.list(session["grant_id"], query_params).data
        return jsonify(messages)
    except Exception as e:
        return f'Error fetching emails: {str(e)}', 500

if __name__ == "__main__":
    if any(value is None for value in nylas_config.values()):
        print("Error: Some configuration values are None. Please check your environment variables.")
    else:
        print("Configuration loaded successfully:")
        print(f"Server running on http://localhost:5002")
        print(f"Callback URI configured as: {nylas_config['callback_uri']}")
        app.run(host='0.0.0.0', port=5002, debug=True)   