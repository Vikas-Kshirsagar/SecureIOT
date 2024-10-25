// static/js/packets.js
function updatePacketTable() {
    fetch('/api/packets/recent')
        .then(response => response.json())
        .then(packets => {
            const tableBody = document.getElementById('packetTable');
            const packetsHtml = packets.map(packet => `
                <tr>
                    <td>${new Date(packet.timestamp).toLocaleTimeString()}</td>
                    <td>${packet.src_ip}:${packet.src_port}</td>
                    <td>${packet.dst_ip}:${packet.dst_port}</td>
                    <td>${packet.protocol}</td>
                    <td>${packet.is_encrypted ? 'Yes' : 'No'}</td>
                </tr>
            `).join('');
            tableBody.innerHTML = packetsHtml;
        });
}

setInterval(updatePacketTable, 5000);
updatePacketTable();