document.addEventListener('DOMContentLoaded', function () {

  // Existing code for auto-moving to next input box
  // ... (if needed) ...

  // Add this event listener
  document.getElementById('activatePal').addEventListener('click', function (e) {
    e.preventDefault();

    // Replace this section with how you want to fetch the phone number
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

});
