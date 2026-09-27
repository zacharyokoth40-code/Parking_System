const payBtn = document.getElementById("pay-btn");
if (payBtn) {
  payBtn.addEventListener("click", async () => {
    const box = document.getElementById("quote-box");
    const entryId = box.dataset.entryId;
    const amount = box.dataset.amount;
    const method = document.getElementById("method").value;
    const resultDiv = document.getElementById("pay-result");
    resultDiv.innerHTML = "Processing payment...";

    try {
      const payRes = await fetch("/api/pay", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entry_id: entryId, amount: amount, method: method }),
      });
      const payData = await payRes.json();
      if (!payRes.ok) throw new Error(payData.message);

      const barrierRes = await fetch("/api/exit/open-barrier", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entry_id: entryId }),
      });
      const barrierData = await barrierRes.json();
      if (!barrierRes.ok) throw new Error(barrierData.message);

      resultDiv.innerHTML =
        `<div class="ticket">Payment confirmed. Receipt: ${payData.receipt_no}<br>` +
        `Barrier: ${barrierData.barrier}. Safe travels!</div>`;
      payBtn.disabled = true;
    } catch (err) {
      resultDiv.innerHTML = `<div class="error-box">${err.message}</div>`;
    }
  });
}
