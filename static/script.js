document.addEventListener('DOMContentLoaded', function () {

  // Additional code for auto-moving to next input box
  for (let i = 1; i <= 10; i++) {
    const inputBox = document.getElementById(`input${i}`);
    inputBox.addEventListener('input', function () {
      if (i < 10) {
        document.getElementById(`input${i + 1}`).focus();
      }
    });
  }

  // Your existing code for form submission
  document.getElementById('phoneNumberForm').addEventListener('submit', function (e) {
    e.preventDefault();

    // Combine all the single numbers from the 10 input boxes to make the full phone number
    let phoneNumber = '';
    for (let i = 1; i <= 10; i++) {
      phoneNumber += document.getElementById(`input${i}`).value;
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
});
