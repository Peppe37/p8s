# How to Configure Social Login (OAuth2)

P8s supports OAuth2 authentication out of the box for Google, GitHub, and Microsoft.

## Step 1: Obtain Provider Credentials

1.  **Google:** Go to [Google Cloud Console](https://console.cloud.google.com/), create credentials for an OAuth2 Client ID.
2.  **GitHub:** Go to Developer Settings > OAuth Apps > New OAuth App.
3.  **Microsoft:** Register an app in the Azure Portal.

Set the callback URL to: `http://localhost:8000/auth/social/callback/{provider_name}` (e.g., `google`, `github`).

## Step 2: Configure Settings

Add the provider configuration to your `backend/settings.py` (or environment variables):

```python
# backend/settings.py
from p8s.core.settings import Settings

class ProjectSettings(Settings):
    # ... other settings ...

    OAUTH2_PROVIDERS = {
        "google": {
            "client_id": "YOUR_GOOGLE_CLIENT_ID",
            "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
        },
        "github": {
            "client_id": "YOUR_GITHUB_CLIENT_ID",
            "client_secret": "YOUR_GITHUB_CLIENT_SECRET",
            "scope": "user:email",
        },
    }
```

> **Security Tip:** Never commit secrets! Use environment variables like `GOOGLE_CLIENT_ID` and load them in your settings.

## Step 3: Frontend Integration

The backend exposes endpoints at:
- Login: `/auth/social/login/{provider}`
- Callback: `/auth/social/callback/{provider}`

In your frontend login page, add buttons linking to these endpoints:

```html
<a href="http://localhost:8000/auth/social/login/google">Login with Google</a>
<a href="http://localhost:8000/auth/social/login/github">Login with GitHub</a>
```

## Step 4: Verify

1.  Click the login link.
2.  Authenticate with the provider.
3.  You will be redirected back to your app with a session cookie or JWT token.
4.  A `SocialAccount` record will be created and linked to the `User`.
