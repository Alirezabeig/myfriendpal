document.addEventListener('DOMContentLoaded', function () {
  console.log("DOM Content Loaded");  // Debug line

  const activatePalDiv = document.getElementById('activatePal');

  if (activatePalDiv) {
    console.log("Found Activate Pal div");  // Debug line
    activatePalDiv.addEventListener('click', function (e) {
      console.log("Clicked Activate Pal");  // Debug line
      e.preventDefault();

      const phoneNumber = document.getElementById('phoneInput').value;

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
