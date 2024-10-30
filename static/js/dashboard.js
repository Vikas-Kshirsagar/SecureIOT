// static/js/dashboard.js
function renderCharts() {
    fetch('/api/traffic-stats')
        .then(response => response.json())
        .then(data => {
            // Pie chart for Encrypted vs Unencrypted Traffic
            new Chart(document.getElementById('trafficChart'), {
                type: 'pie',
                data: {
                    labels: ['Encrypted', 'Unencrypted'],
                    datasets: [{
                        data: [data.encrypted, data.unencrypted],
                        backgroundColor: ['#4CAF50', '#F44336'],
                    }]
                }
            });

            // Bar chart for Device Types
            new Chart(document.getElementById('deviceTypeChart'), {
                type: 'bar',
                data: {
                    labels: Object.keys(data.device_types),
                    datasets: [{
                        label: 'Device Types',
                        data: Object.values(data.device_types),
                        backgroundColor: '#3E95CD',
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });
}

function updateDashboard() {
    // Update device stats
    fetch('/api/devices')
        .then(response => response.json())
        .then(devices => {
            const stats = {
                total: devices.length,
                active: devices.filter(d => new Date(d.last_seen) > new Date(Date.now() - 300000)).length,
                types: {}
            };
            
            devices.forEach(device => {
                stats.types[device.type] = (stats.types[device.type] || 0) + 1;
            });

            const statsHtml = `
                <p>Total Devices: ${stats.total}</p>
                <p>Active Devices: ${stats.active}</p>
                <div class="mt-2">
                    <h3 class="font-bold">Device Types:</h3>
                    ${Object.entries(stats.types)
                        .map(([type, count]) => `<p>${type}: ${count}</p>`)
                        .join('')}
                </div>
            `;
            document.getElementById('deviceStats').innerHTML = statsHtml;
        });

    // Update recent packets
    fetch('/api/packets/recent')
        .then(response => response.json())
        .then(packets => {
            const recentPacketsHtml = packets.slice(0, 5).map(packet => `
                <div class="border-b py-2">
                    <p class="text-sm text-gray-600">${new Date(packet.timestamp).toLocaleTimeString()}</p>
                    <p>${packet.src_ip}:${packet.src_port} → ${packet.dst_ip}:${packet.dst_port}</p>
                </div>
            `).join('');
            document.getElementById('recentPackets').innerHTML = recentPacketsHtml;
        });

    // Fetch and render charts
    renderCharts();
}

setInterval(updateDashboard, 5000); // for dashboard.html
updateDashboard()