capacity = 1;

document.getElementById("capacity").addEventListener("change", (event) => {
  capacity = parseInt(event.target.value);
  updateFares();
});

function updateFares() {
  document.querySelectorAll(".fare").forEach((el) => {
    el.textContent = (parseInt(el.getAttribute("data-fare")) / capacity)
      .toFixed(
        0,
      );
  });
}

document.getElementById("capacity").selectedIndex = 0;

updateFares();
