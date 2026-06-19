// PyCompilerApp/static/PyCompilerApp/main.js
let editor;
let socket;
let consoleDiv;
let currentInput = "";

// Helper to keep the cursor at the end
function updateTerminalDisplay(text = "") {
    // Remove existing cursor if any
    const existingCursor = consoleDiv.querySelector('.cursor');
    if (existingCursor) existingCursor.remove();

    if (text) {
        consoleDiv.innerText += text;
    }
    
    // Append the cursor element
    const cursor = document.createElement('span');
    cursor.className = 'cursor';
    consoleDiv.appendChild(cursor);
    
    // Auto-scroll
    consoleDiv.scrollTop = consoleDiv.scrollHeight;
}

require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' } });
require(['vs/editor/editor.main'], function () {
    editor = monaco.editor.create(document.getElementById('editor'), {
        value: `print("Hello from Django!")\nx = input("Enter value: ")\nprint("You typed:", x)`,
        language: 'python',
        theme: 'vs-dark',
        automaticLayout: true
    });
});

function runCode() {
    consoleDiv = document.getElementById("console");
    consoleDiv.innerHTML = ""; 
    currentInput = "";
    updateTerminalDisplay(); // Initialize cursor
    consoleDiv.focus();

    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/run/`);

    socket.onopen = () => {
        socket.send(editor.getValue());
    };

    socket.onmessage = (event) => {
        updateTerminalDisplay(event.data);
    };
}

document.getElementById("console").addEventListener("keydown", function(e) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;

    if (e.key === "Enter") {
        e.preventDefault();
        socket.send(currentInput + "\n");
        updateTerminalDisplay("\n");
        currentInput = "";
    } else if (e.key === "Backspace") {
        e.preventDefault();
        if (currentInput.length > 0) {
            currentInput = currentInput.slice(0, -1);
            // Re-render the text minus last char + cursor
            const text = consoleDiv.innerText;
            consoleDiv.innerText = text.slice(0, -1);
            updateTerminalDisplay();
        }
    } else if (e.key.length === 1) {
        currentInput += e.key;
        updateTerminalDisplay(e.key);
    }
});