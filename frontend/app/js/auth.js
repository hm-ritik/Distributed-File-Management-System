
const loginForm = document.getElementById("loginForm");
const loginButton = document.getElementById("loginButton");
const loginMessage = document.getElementById("loginMessage");


// Redirect to dashboard if already logged in
if (getToken()) {
    window.location.href = "dashboard.html";
}


// Login Form Submission
loginForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    if (!email || !password) {
        showMessage(
            "Please enter email and password.",
            "error"
        );
        return;
    }

    loginButton.disabled = true;
    loginButton.textContent = "Logging in...";

    clearMessage();

    try {

        const response = await login(email, password);
        const data = await response.json();

        if (response.ok) {

            saveToken(data.access_token);

            showMessage(
                "Login successful.",
                "success"
            );

            setTimeout(() => {
                window.location.href = "dashboard.html";
            }, 500);

        } else {

            showMessage(
                data.detail || "Login failed.",
                "error"
            );
        }

    } catch (error) {

        console.error("Login error:", error);

        showMessage(
            "Unable to connect to the server.",
            "error"
        );

    } finally {

        loginButton.disabled = false;
        loginButton.textContent = "Login";
    }
});


// Display Login Messages
function showMessage(message, type) {

    loginMessage.textContent = message;
    loginMessage.className = `message ${type}`;
}


// Clear Login Messages
function clearMessage() {

    loginMessage.textContent = "";
    loginMessage.className = "message";
}


// Recruiter Demo Account
const demoButton = document.getElementById("useDemoAccount");

if (demoButton) {

    demoButton.addEventListener("click", function () {

        document.getElementById("email").value =
            "dummyaccount@gmail.com";

        document.getElementById("password").value =
            "23cse233";

        clearMessage();

    });

}


