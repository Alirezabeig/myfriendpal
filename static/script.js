document.getElementById('phoneNumberForm').addEventListener('submit', function(e) {
  e.preventDefault();
  let phoneNumber = document.getElementById('phoneNumber').value;
  
  fetch('/sendSMS', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ phoneNumber: phoneNumber })
  })
  .then(response => response.json())
  .then(data => {
    console.log(data.message);
  });
});
