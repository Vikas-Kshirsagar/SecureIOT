// static/js/notifications.js
document.addEventListener('DOMContentLoaded', function() {
    const bell = document.getElementById('notificationBell');
    const panel = document.getElementById('notificationPanel');
    const count = document.getElementById('notificationCount');
    const list = document.getElementById('notificationList');

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
            refreshNotificationCount();
        }
    });

    // Fetch notifications
    function fetchNotifications() {
        fetch('/api/notifications')
            .then(response => response.json())
            .then(notifications => {
                updateNotificationCount(notifications.length);
                displayNotifications(notifications);
            });
    }

    // Update notification count
    function updateNotificationCount(number) {
        count.textContent = number;
        count.classList.toggle('hidden', number === 0);
    }

    // Display notifications in panel
    function displayNotifications(notifications) {
        if (notifications.length === 0) {
            list.innerHTML = '<div class="text-gray-500 text-center">No new notifications</div>';
            return;
        }

        list.innerHTML = notifications.map(notification => `
            <a href="/api/notification/${notification.id}" class="block notification-item bg-gray-50 p-3 rounded hover:bg-gray-100" data-id="${notification.id}">
                <div class="font-bold text-sm">${notification.device_name}</div>
                <div class="text-sm text-gray-600">IP: ${notification.device_ip}</div>
                <div class="text-sm mt-1">${notification.message}</div>
                <div class="text-xs text-gray-500 mt-1">
                    ${new Date(notification.created_at).toLocaleString()}
                </div>
            </a>
        `).join('');
    }



    // Check and refresh notification count (in case of background updates)
    function refreshNotificationCount() {
        fetch('/api/notifications')
            .then(response => response.json())
            .then(notifications => {
                updateNotificationCount(notifications.length);
            });
    }

    // Initial fetch without marking read
    fetchNotifications();

    // Fetch notifications every 30 seconds without auto-marking them as read
    setInterval(fetchNotifications, 30000);
});
