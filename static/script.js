/* For index.html */

// TODO: If a user clicks to create a chat, create an auth key for them
// and save it. Redirect the user to /chat/<chat_id>
function createChat() {

}


// TODO: Fetch the list of existing chat messages.
// POST to the API when the user posts a new message.
// Automatically poll for new messages on a regular interval.
function postMessage(roomId, comment) {
  fetch(`/api/rooms/${roomId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Api-Key': WATCH_PARTY_API_KEY, // 这里应替换为实际的 API 密s钥管理方式
    },
    body: JSON.stringify({ body: comment })
  })
  .then(response => response.json())
  .then(() => {
    commentInput.value = ''; // 清空输入框
  })
}

function getMessages(roomId) {
  
  fetch(`/api/rooms/${roomId}/messages`,  {headers: {
    'Api-Key': WATCH_PARTY_API_KEY,
  }})
    .then(response => response.json())
    .then(messages => {
        const messagesContainer = document.querySelector('.messages');
        messagesContainer.innerHTML = ''; // Clear existing messages
        messages.forEach(message => {
          const messageElement = document.createElement('message');
          const authorElement = document.createElement('author');
          authorElement.textContent = message.name; 
          const contentElement = document.createElement('content');
          console.log(contentElement)
          contentElement.textContent = message.body;
          messageElement.appendChild(authorElement);
          messageElement.appendChild(contentElement);
          messagesContainer.appendChild(messageElement);
      });
    })
    .catch(error => console.error('Error fetching messages:', error));
}

function startMessagePolling() {
  const roomId = window.location.pathname.split('/')[2]; 
  setInterval(() => {
    getMessages(roomId);
  }, 100); 
}

function startMessagePolling() {
  return;
}

document.addEventListener('DOMContentLoaded', function() {
  const roomId = window.location.pathname.split('/')[2];
  getMessages(roomId);
});



document.addEventListener('submit', function() {
  const commentInput = document.querySelector('textarea[name="comment"]');
  const comment = commentInput.value;
  const roomId = window.location.pathname.split('/')[2];
  console.log("commentInput"); 

  postMessage(roomId, comment)
  //.catch(error => console.error('Error:', error));
});


document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('update-username-btn').addEventListener('click', function() {
    const newUsername = document.getElementById('username-input').value;
    updateUserInfo('/api/user/name', {new_username: newUsername});
})
});

document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('update-password-btn').addEventListener('click', function() {
    const newPassword = document.getElementById('password-input').value;
    updateUserInfo('/api/user/password', {new_password: newPassword});
  });
});


function updateUserInfo(url, data) {
  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Api-Key': WATCH_PARTY_API_KEY,
    },
    body: JSON.stringify(data)
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  })
  .then(data => {
    console.log('Success:', data);
  })
  .catch((error) => {
    console.error('Error:', error);
  });
}



function updateRoomName() {
  const inviteLink = document.querySelector(".invite")
  const text = inviteLink.getElementsByTagName('a')[0].innerHTML
  const room_id = Number(text.slice(text.length - 1))
  const room_name = document.getElementById("room_name_input").value
  const url = `/api/rooms/${room_id}`
  fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Api-Key': WATCH_PARTY_API_KEY
      },
      body: JSON.stringify({name: room_name})
  })
  .then(response => response.json())
      .then(() => {
          document.getElementById("room_name_span").value = room_name
          document.querySelector(".roomData .edit").classList.add("hide");
          document.querySelector(".roomData .display").classList.remove("hide");
          alert('Room name updated successfully');
          location.reload(true);
      })
  .catch(error => console.error(`Error: ${error}`));
}

function toggleHide() {
  document.querySelector(".roomData .edit").classList.remove("hide");
  document.querySelector(".roomData .display").classList.add("hide");
}

