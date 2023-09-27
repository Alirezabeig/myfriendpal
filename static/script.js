document.addEventListener('DOMContentLoaded', function () {
  console.log("DOM Content Loaded");  // Debug line

  // Initialize hover messages
  const hoverMessages = {
      "phrase1": "I'm like a 24/7 diner, open for texts anytime.",
      "phrase2": "I'm a blend of Einstein and a stand-up comedian.",
      "phrase3": "Busier than a lazy cat, which means never.",
      "phrase4": "Solving your puzzles is my daily Sudoku game.",
      "phrase5": "Impress you? You'll think I'm a magician!",
      "phrase6": "We'll click so well, you'd think I'm a mind reader."
  };

  // Add tooltip text for all phrases
    for (let i = 1; i <= 6; i++) {
      const phrase = document.getElementById(`phrase${i}`);
      if (phrase) {
        const tooltip = phrase.querySelector('.tooltip');
        tooltip.innerText = hoverMessages[`phrase${i}`];
        phrase.addEventListener("mouseover", function() {
          tooltip.style.visibility = "visible";
          tooltip.style.opacity = "1";
        });
        phrase.addEventListener("mouseout", function() {
          tooltip.style.visibility = "hidden";
          tooltip.style.opacity = "0";
        });
      }
    }

  const activatePalDiv = document.getElementById('activatePal');

  if (activatePalDiv) {
    console.log("Found Activate Pal div");  // Debug line
    activatePalDiv.addEventListener('click', function (e) {
      console.log("Clicked Activate Pal");  // Debug line
      e.preventDefault();

      const phoneNumber = document.getElementById('phoneInput').value;

      // Validate phone number
      if (!phoneNumber) {
        alert("Please enter your phone number");
        return;
      }

      fetch('/send_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ phone_number: phoneNumber })
      })
      .then(response => response.json())
      .then(data => alert(data.message))
      .catch(error => alert('Failed to send SMS. Please try again.'));
    });
  } else {
    console.log("Could not find Activate Pal div");  // Debug line
  }
});
