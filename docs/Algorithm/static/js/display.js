// Polls /api/slots every 3s so the board reflects entries/exits live.
async function refreshBoard() {
  const res = await fetch("/api/slots");
  const data = await res.json();

  document.getElementById("total").textContent = data.counts.total;
  document.getElementById("free").textContent = data.counts.free;
  document.getElementById("occupied").textContent = data.counts.occupied;

  const grid = document.getElementById("slot-grid");
  grid.innerHTML = "";
  data.slots.forEach(slot => {
    const div = document.createElement("div");
    div.className = `slot ${slot.status}`;
    div.textContent = slot.bay_number;
    grid.appendChild(div);
  });
}

refreshBoard();
setInterval(refreshBoard, 3000);
