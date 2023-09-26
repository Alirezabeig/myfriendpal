document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('phoneNumberForm').addEventListener('submit', function (e) {
    e.preventDefault();

    let phoneNumber = document.getElementById('phoneNumber').value;

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

