document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('phoneNumberForm').addEventListener('submit', function (e) {
      console.log("form submitted")
    e.preventDefault();

    let phoneNumber = document.getElementById('phoneNumber').value;

    fetch('/send_message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ phone_number: phoneNumber })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        console.log(data.message);
        alert(data.message);
      })
      .catch(error => {
        console.error('Error:', error);
        alert('Failed to send SMS. Please try again.');
      });
  });
});

