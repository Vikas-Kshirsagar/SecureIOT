// static/js/devices.js
function updateDevices() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(devices => {
            const tableBody = document.getElementById('deviceTable');
            const tableHtml = devices.map(device => `
                <tr>
                    <td class="px-4 py-2">${device.name}</td>
                    <td class="px-4 py-2">${device.ip}</td>
                    <td class="px-4 py-2">${device.mac}</td>
                    <td class="px-4 py-2">${device.type}</td>
                    <td class="px-4 py-2">${device.os || 'Unknown'}</td>
                    <td class="px-4 py-2">${device.open_ports ? device.open_ports.join(', ') : 'None'}</td>
                    <td class="px-4 py-2">${new Date(device.last_seen).toLocaleString()}</td>
                </tr>
            `).join('');
            tableBody.innerHTML = tableHtml;
        });
}
setInterval(updateDevices, 5000);   // for devices.html
updateDevices()
