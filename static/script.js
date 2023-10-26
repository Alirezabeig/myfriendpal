document.addEventListener('DOMContentLoaded', function () {
  console.log("DOM Content Loaded");

  const activatePalButton = document.getElementById('activatePal');

  if (activatePalButton) {
    console.log("Found Activate Pal button");
    activatePalButton.addEventListener('click', function (e) {
      console.log("Clicked Activate Pal");
      e.preventDefault();

      const phoneNumber = document.getElementById('phoneInput').value;

      // Initialize modal components
      const modal = document.getElementById("myModal");
      const span = document.getElementsByClassName("close")[0];
      const modalText = document.getElementById("modalText");
      const modalBulletPoints = document.getElementById("modalBulletPoints");

      // Validate phone number
      if (!phoneNumber) {
        modalText.innerText = "Please enter your phone number";
        modal.style.display = "block";

        span.onclick = function () {
          modal.style.display = "none";
        };

        window.onclick = function (event) {
          if (event.target === modal) {
            modal.style.display = "none";
          }
        };

        return;
      }

      // Sending message
      fetch('/send_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ phone_number: phoneNumber })
      })
        .then(response => {
          if (response.ok) {
            return response.json();
          } else {
            throw new Error('Failed to send SMS. Please try again.');
          }
        })
        .then(data => {
          modalText.innerText = "Great! Pal is now going to message you on your phone to pick up the conversation.";
          modalBulletPoints.innerHTML = `
            <li>Your first random point</li>
            <li>Your second random point</li>
            <li>Your third random point</li>
          `;

          modal.style.display = "block";

          span.onclick = function () {
            modal.style.display = "none";
          };

          window.onclick = function (event) {
            if (event.target === modal) {
              modal.style.display = "none";
            }
          };
        })
        .catch(error => {
          modalText.innerText = error.message; // Display the error message
          modal.style.display = "block";
        });
    });
  } else {
    console.log("Could not find Activate Pal button");
  }
});
