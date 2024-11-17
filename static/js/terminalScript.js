const inputField = document.getElementById('input');
const outputDiv = document.getElementById('output');
let commandHistory = []; // Store the command history
let historyIndex = -1;  // Keep track of the current history index

// Display the initial "UQI" pattern or greeting
window.onload = () => {
  //outputDiv.innerHTML += `<div class="command"><span class="output-text">UQI - Unified Query Interface || Developed By Arwaz, Affan and Saurabh</span></div>`;
  outputDiv.innerHTML += `<div class="command"><img src="static/images/banner.png" alt="UQI Logo" class="output-image"></div>`;

  outputDiv.innerHTML += `<div class="command"><span class="output-text">Type 'help' for available commands.</span></div>`;
};

inputField.addEventListener('keydown', function (event) {
  if (event.key === 'Enter') {
    const command = inputField.value.trim();
    inputField.value = '';
    sendCommandToServer(command);
  } else if (event.key === 'ArrowUp') {
    // Recall the last command when pressing the up arrow key
    if (historyIndex > 0) {
      historyIndex--;
      inputField.value = commandHistory[historyIndex];
    }
  } else if (event.key === 'ArrowDown') {
    // Go forward in the command history if possible
    if (historyIndex < commandHistory.length - 1) {
      historyIndex++;
      inputField.value = commandHistory[historyIndex];
    } else {
      inputField.value = '';  // If we're at the most recent command, clear input
    }
  }
});

function sendCommandToServer(command) {
  // Add the command to the history if it's not 
  if (command) {
    commandHistory.push(command);
    historyIndex = commandHistory.length;  // Reset historyIndex after a new command
  }

  if (command === 'docs') {
    // Open the PDF directly in a new window
    window.open('/static/docs.pdf', '_blank');
    return; // Prevent further handling of the command
  } else if (command === 'exit') {
    // Close the window when 'exit' is typed
    window.close();
    return; // Prevent further handling of the command
  } else if (command === 'animate') {
    // Show the GIF without calling the server
    displayGif();
    return;
  }

  fetch('/command', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ command: command })
  })
    .then(response => response.json())
    .then(data => {
      const commandOutput = data.response;

      if (commandOutput === 'clear') {
        outputDiv.innerHTML = '';  // Clear the output area
      } else {
        // Add space between the previous output and the new command
        outputDiv.innerHTML += `<div class="command-space"></div>`; // Space added here

        // Always display the original input command with no color change
        outputDiv.innerHTML += `<div class="command"><span class="prompt">>> </span><span class="input-command">${command}</span></div>`;

        // Check if the command output contains an error message
        if (commandOutput.includes("Command not recognized") || commandOutput.includes("Error")) {
          // Apply the 'error-output' class to just the output text when error occurs
          outputDiv.innerHTML += `<div class="command"><span class="error-output">${commandOutput}</span></div>`;
        } else {
          // Regular output with yellow color
          outputDiv.innerHTML += `<div class="command"><span class="output-text">${commandOutput}</span></div>`;
        }
      }
      outputDiv.scrollTop = outputDiv.scrollHeight;
    })
    .catch(error => {
      // If there's a fetch error, display in red color using 'error-output' class
      outputDiv.innerHTML += `<div class="command"><span class="error-output">Error: ${error}</span></div>`;
    });
}


function displayGif() {
  const gifDiv = document.createElement('div');
  gifDiv.classList.add('gif-container');
  gifDiv.innerHTML = `
    <img src="static/images/animation.webp" alt="Loading Animation" class="gif-animation">
  `;

  outputDiv.appendChild(gifDiv);

  // Automatically remove the GIF after it completes
  setTimeout(() => {
    gifDiv.remove();
  }, 5000); // Adjust this duration based on your GIF length
}