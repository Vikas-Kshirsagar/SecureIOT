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

// Updated notifications.js
document.addEventListener('DOMContentLoaded', function() {
    const bell = document.getElementById('notificationBell');
    const panel = document.getElementById('notificationPanel');
    const count = document.getElementById('notificationCount');
    const list = document.getElementById('notificationList');
    let notifications = {};

    // Toggle notification panel
    bell.addEventListener('click', function(e) {
        e.stopPropagation();
        panel.classList.toggle('hidden');
        if (!panel.classList.contains('hidden')) {
            fetchNotifications();
        }
    });

    // Close panel when clicking outside
    document.addEventListener('click', function(e) {
        if (!panel.contains(e.target) && !bell.contains(e.target)) {
            panel.classList.add('hidden');
        }
    });

    // Fetch notifications and group by device
    function fetchNotifications() {
        fetch('/api/notifications')
            .then(response => response.json())
            .then(data => {
                // Group notifications by device_ip
                notifications = data.reduce((acc, notification) => {
                    if (!acc[notification.device_ip] || 
                        new Date(acc[notification.device_ip].created_at) < new Date(notification.created_at)) {
                        acc[notification.device_ip] = notification;
                    }
                    return acc;
                }, {});
                
                updateNotificationCount(Object.keys(notifications).length);
                displayNotifications(Object.values(notifications));
            });
    }

    // Update notification count
    function updateNotificationCount(number) {
        count.textContent = number;
        count.classList.toggle('hidden', number === 0);
    }

    // Display notifications in panel
    function displayNotifications(notificationArray) {
        if (notificationArray.length === 0) {
            list.innerHTML = '<div class="text-gray-500 text-center">No new notifications</div>';
            return;
        }

        list.innerHTML = notificationArray.map(notification => `
            <div class="notification-item bg-gray-50 p-3 rounded hover:bg-gray-100 cursor-pointer" 
                 data-id="${notification.id}" onclick="markAsRead(${notification.id})">
                <div class="font-bold text-sm">${notification.device_name}</div>
                <div class="text-sm text-gray-600">IP: ${notification.device_ip}</div>
                <div class="text-sm mt-1">${notification.message}</div>
                <div class="text-xs text-gray-500 mt-1">
                    ${new Date(notification.created_at).toLocaleString()}
                </div>
            </div>
        `).join('');

        // Add click handlers for notification items
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', function() {
                const notificationId = this.getAttribute('data-id');
                markNotificationAsRead(notificationId);
            });
        });
    }

    // Mark notification as read
    function markNotificationAsRead(id) {
        fetch('/api/notifications/' + id, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ids: [id] })
        })
        .then(response => response.json())
        .then(() => {
            // Remove the notification from our local storage
            const deviceIp = Object.keys(notifications).find(
                ip => notifications[ip].id === parseInt(id)
            );
            if (deviceIp) {
                delete notifications[deviceIp];
                updateNotificationCount(Object.keys(notifications).length);
                displayNotifications(Object.values(notifications));
            }
        });
    }

    // Initial fetch
    fetchNotifications();

    // Fetch notifications every 30 seconds
    setInterval(fetchNotifications, 30000);
});