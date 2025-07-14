document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("user-search");
  const clearBtn = document.querySelector(".clear-search");
  const userRows = document.querySelectorAll("#users-table tbody tr");

  // Toggle clear button visibility
  searchInput.addEventListener("input", function () {
    const searchTerm = this.value.toLowerCase();
    clearBtn.classList.toggle("d-none", searchTerm === "");

    // Filter rows
    userRows.forEach((row) => {
      const textContent = row.textContent.toLowerCase();
      row.style.display = textContent.includes(searchTerm) ? "" : "none";
    });
  });

  // Clear search functionality
  clearBtn.addEventListener("click", function () {
    searchInput.value = "";
    searchInput.focus();
    clearBtn.classList.add("d-none");

    // Show all rows
    userRows.forEach((row) => {
      row.style.display = "";
    });
  });
});
