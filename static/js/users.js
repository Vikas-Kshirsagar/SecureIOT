// static/js/users.js
function updateUsers() {
    fetch('/api/users')
        .then(response => response.json())
        .then(users => {
            const usersList = document.getElementById('usersList');
            usersList.innerHTML = users.map(user => `
                <tr class="border-t hover:bg-gray-50">
                    <td class="px-4 py-2">${user.username}</td>
                    <td class="px-4 py-2">${user.email}</td>
                    <td class="px-4 py-2">${user.age}</td>
                    <td class="px-4 py-2">${user.phone}</td>
                    <td class="px-4 py-2">${user.address}</td>
                    <td class="px-4 py-2">${new Date(user.created_at).toLocaleString()}</td>
                </tr>
            `).join('');
        });
}

// Initial load
updateUsers();
// Refresh every 30 seconds
setInterval(updateUsers, 30000);
