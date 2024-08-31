console.log("JavaScript file loaded");

const userId = "cli_user_" + Math.random().toString(36).substring(2, 15); // Egyedi user_id generálása

const host = window.location.hostname;

function createWebSocket() {
    const ws = new WebSocket(`ws://${host}:8081/ws/${userId}`);

    ws.onopen = function(event) {
        console.log("WebSocket connection established", event);
    };

    ws.onmessage = function(event) {
        const message = event.data;

        // Szűrjük ki a "ping" üzeneteket
        if (message === "ping") {
            console.log("Ping received from server, no action taken");
            return;  // Ne jelenjen meg a kliens felületen
        }

        console.log("Message received from server:", message);
        addMessageToChatbox("agent", message);
    };

    ws.onerror = function(event) {
        console.error("WebSocket error observed:", event);
    };

    ws.onclose = function(event) {
        console.log("WebSocket connection closed", event);

        // Próbálj újracsatlakozni 1 másodperc múlva
        setTimeout(createWebSocket, 1000);
    };

    return ws;
}

let ws = createWebSocket();

async function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (message === "") return;

    // Add the user message to the chatbox
    addMessageToChatbox("user", message);
    input.value = "";

    // Send the message to the server
    const response = await fetch("/cli/events", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: message, user_id: userId })  // Egyedi user_id továbbítása
    });

    const data = await response.json();
    if (data.message) {
        console.log("Message sent to server:", message);
        // The WebSocket server will handle the agent's response
    }

    // Fókusz visszaállítása az input mezőre az üzenet elküldése után
    input.focus();
}

function addMessageToChatbox(sender, message) {
    const chatbox = document.getElementById("chatbox");
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);

    const bubbleDiv = document.createElement("div");
    bubbleDiv.classList.add("bubble");

    // Use <pre> to preserve newlines and whitespace
    const preElement = document.createElement("pre");
    preElement.textContent = message;
    bubbleDiv.appendChild(preElement);

    messageDiv.appendChild(bubbleDiv);
    chatbox.appendChild(messageDiv);

    // Scroll to the bottom after adding a message
    chatbox.scrollTop = chatbox.scrollHeight;
}

function printChat() {
    window.print();
}

// Fókusz az input mezőre az oldal betöltésekor
window.onload = function() {
    document.getElementById("user-input").focus();
};
