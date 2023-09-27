document.addEventListener('DOMContentLoaded', function () {
  console.log("DOM Content Loaded");  // Debug line

  // Initialize hover messages
  const hoverMessages = {
    "phrase1": "I am 24/7 available, so text me anytime",
    "phrase2": "You have never met anyone as smart and fun as I am.",
    "phrase3": "I am always here and never busy with anything else",
    "phrase4": "I'd love to help you with any challenge you have anytime.",
    "phrase5": "I will amaze you if you get easily amazed :)",
    "phrase6": "We will build real connection as I everyday learn about you"
      // Add hover event listeners for all phrases
      for (let i = 1; i <= 6; i++) {
          const phrase = document.getElementById(`phrase${i}`);
          if (phrase) {
              const tooltip = phrase.querySelector('.tooltip');
           tooltip.innerText = hoverMessages[`phrase${i}`];
         }
       }

  };

  // Add hover event listeners for all phrases
  for (let i = 1; i <= 6; i++) {
    const phrase = document.getElementById(`phrase${i}`);
    if (phrase) {
      phrase.addEventListener("mouseover", function() {
        alert(hoverMessages[`phrase${i}`]);
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
