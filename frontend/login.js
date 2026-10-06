const API_ROOT = window.location.port === "8001"
    ? `${window.location.protocol}//${window.location.hostname}:8000`
    : window.location.origin;
const API_URL = `${API_ROOT}/api`;
const USER_SESSION_KEY = "resumePilot.googleUser";
const googleStatus = document.getElementById("googleStatus");
const googleButton = document.getElementById("googleSignInButton");
let googleInitialized = false;

function setGoogleStatus(message, isError = false) {
    googleStatus.textContent = message;
    googleStatus.classList.toggle("error", isError);
}

async function initializeGoogleSignIn() {
    if (googleInitialized || !window.google?.accounts?.id) return;
    googleInitialized = true;

    try {
        const configResponse = await fetch(`${API_URL}/auth/google/config`);
        const config = await configResponse.json().catch(() => ({}));
        if (!configResponse.ok || !config.client_id) {
            throw new Error(config.detail || "Google sign-in is not configured on the API.");
        }

        window.google.accounts.id.initialize({
            client_id: config.client_id,
            callback: handleGoogleCredential,
            auto_select: false,
            cancel_on_tap_outside: true,
        });
        window.google.accounts.id.renderButton(googleButton, {
            type: "standard",
            theme: "outline",
            size: "large",
            text: "continue_with",
            shape: "pill",
            logo_alignment: "left",
            width: Math.min(360, Math.floor(googleButton.getBoundingClientRect().width)),
        });
        setGoogleStatus("Continue securely with your Google account.");
    } catch (error) {
        const detail = error instanceof TypeError
            ? "The API is unavailable. Start the backend and configure GOOGLE_CLIENT_ID."
            : `${error.message} Set GOOGLE_CLIENT_ID in the backend .env file.`;
        setGoogleStatus(detail, true);
    }
}

async function handleGoogleCredential(response) {
    if (!response?.credential) {
        setGoogleStatus("Google did not return an identity credential. Please try again.", true);
        return;
    }

    setGoogleStatus("Verifying your Google account…");
    try {
        const verification = await fetch(`${API_URL}/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ credential: response.credential }),
        });
        const profile = await verification.json().catch(() => ({}));
        if (!verification.ok) {
            throw new Error(profile.detail || "Google sign-in could not be verified.");
        }

        sessionStorage.setItem(USER_SESSION_KEY, JSON.stringify({
            subject: profile.subject,
            name: profile.name,
            email: profile.email,
            picture: profile.picture,
        }));
        window.location.assign("index.html");
    } catch (error) {
        setGoogleStatus(error.message, true);
    }
}

const googleScript = document.getElementById("googleIdentityScript");
if (googleScript) {
    googleScript.addEventListener("load", initializeGoogleSignIn, { once: true });
    googleScript.addEventListener("error", () => setGoogleStatus("Google sign-in could not load. Check your internet connection.", true), { once: true });
}
if (window.google?.accounts?.id) initializeGoogleSignIn();
