function loadDeviceInfo() {
    const ipAddress = window.location.pathname.split('/').pop();
    fetch(`/api/device-info/${ipAddress}`)
        .then(response => response.json())
        .then(info => {
            document.getElementById('deviceIp').textContent = info.device_ip;
            document.getElementById('username').textContent = info.username || 'null';
            document.getElementById('password').textContent = info.password || 'null';
            
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

    // Load connected hosts
    fetch(`/api/device-hosts/${ipAddress}`)
        .then(response => response.json())
        .then(hosts => {
            const hostsInfo = document.getElementById('hostsInfo');
            hostsInfo.innerHTML = '';
            
            if (hosts.length > 0) {
                hosts.forEach(host => {
                    const div = document.createElement('div');
                    div.className = 'p-2';
                    div.innerHTML = `
                        <div class="flex justify-between items-center">
                            <div>
                                <span class="font-medium">${host.name || 'Unknown Device'}</span>
                            </div>
                            <span class="text-gray-500 ml-2">(${host.ip})</span>
                            
                        </div>
                    `;
                    hostsInfo.appendChild(div);
                });
            } else {
                hostsInfo.innerHTML = '<div class="p-2">No connected hosts found</div>';
            }
        });
}

function formatDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Initial load and periodic refresh
loadDeviceInfo();
setInterval(loadDeviceInfo, 30000);