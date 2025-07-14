document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
});

function initDashboard() {
  loadClassStats();
  loadDailyChart();
  loadMonthlyChart();
  loadAgeDistribution();

  document
    .getElementById("daily-filter")
    .addEventListener("change", loadDailyChart);
  document
    .getElementById("monthly-filter")
    .addEventListener("change", loadMonthlyChart);
  document
    .getElementById("age-filter")
    .addEventListener("change", loadAgeDistribution);
}

// ========== DAILY CHART ==========
async function loadDailyChart() {
  const days = document.getElementById("daily-filter").value;
  try {
    const res = await fetch(`/api/daily-predictions?days=${days}`);
    const data = await res.json();
    console.log("Daily chart data:", data);
    renderChart("dailyChart", data, "line");
  } catch (err) {
    console.error("Daily chart load failed:", err);
  }
}

// ========== MONTHLY CHART ==========
async function loadMonthlyChart() {
  const months = document.getElementById("monthly-filter").value;
  try {
    const res = await fetch(`/api/monthly-predictions?months=${months}`);
    const data = await res.json();

    // Apply specific colors to each class
    const classColors = {
      Dyskeratotic: "#e74c3c",
      Koilocytotic: "#f39c12",
      Metaplastic: "#2980b9",
      Parabasal: "#1abc9c",
      "Superficial-Intermediate": "#27ae60",
    };

    // Map the colors to the datasets
    const coloredDatasets = data.datasets.map((dataset) => {
      return {
        ...dataset,
        backgroundColor: classColors[dataset.label] || "#cccccc",
        borderColor: classColors[dataset.label] || "#999999",
        borderWidth: 1,
      };
    });

    renderChart(
      "monthlyChart",
      {
        labels: data.labels,
        datasets: coloredDatasets,
      },
      "bar"
    );
  } catch (err) {
    console.error("Monthly chart load failed:", err);
  }
}

// ========== AGE DISTRIBUTION ==========
async function loadAgeDistribution() {
  const filterClass = document.getElementById("age-filter").value;
  let classParam = filterClass;

  switch (filterClass) {
    case "Dyskeratotic":
      classParam = "Dyskeratotic";
      break;
    case "Koilocytotic":
      classParam = "Koilocytotic";
      break;
    case "Metaplastic":
      classParam = "Metaplastic";
      break;
    case "Parabasal":
      classParam = "Parabasal";
      break;
    case "Superficial-Intermediate":
      classParam = "Superficial-Intermediate";
      break;
  }

  try {
    const res = await fetch(`/api/age-distribution?class=${classParam}`);
    const data = await res.json();
    renderChart(
      "ageChart",
      {
        labels: data.labels,
        datasets: [
          {
            label: "Patient Count",
            data: data.values,
            backgroundColor: "blue",
            borderColor: "blue",
          },
        ],
      },
      "bar"
    );
  } catch (err) {
    console.error("Age distribution load failed:", err);
  }
}

// ========== STATS ==========
async function loadClassStats() {
  try {
    const res = await fetch("/api/class-stats");
    const data = await res.json();
    document.getElementById("total-patients").textContent = data.total;
    document.getElementById("dyskeratotic-predictions").textContent =
      data.counts["Dyskeratotic"] || 0;
    document.getElementById("koilocytotic-predictions").textContent =
      data.counts["Koilocytotic"] || 0;
    document.getElementById("metaplastic-predictions").textContent =
      data.counts["Metaplastic"] || 0;
    document.getElementById("parabasal-predictions").textContent =
      data.counts["Parabasal"] || 0;
    document.getElementById("superficial-predictions").textContent =
      data.counts["Superficial-Intermediate"] || 0;
  } catch (err) {
    console.error("Failed to load class stats:", err);
  }
}

// ========== RENDER CHART ==========
const chartInstances = {};

function renderChart(canvasId, data, type = "bar") {
  const canvas = document.getElementById(canvasId);
  if (!canvas) {
    console.warn(`Canvas element with id ${canvasId} not found.`);
    return;
  }

  const ctx = canvas.getContext("2d");
  if (chartInstances[canvasId]) {
    chartInstances[canvasId].destroy();
  }

  // Default options for bar charts
  const defaultBarOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: "0",
      },
      tooltip: {
        mode: "index",
        intersect: false,
      },
    },
    interaction: {
      mode: "nearest",
      axis: "x",
      intersect: false,
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          precision: 0,
        },
      },
    },
  };

  // Default options for line charts
  const defaultLineOptions = {
    ...defaultBarOptions,
    elements: {
      line: {
        tension: 0.3,
      },
    },
  };

  chartInstances[canvasId] = new Chart(ctx, {
    type: type,
    data: {
      labels: data.labels,
      datasets: data.datasets.map((dataset) => ({
        ...dataset,
        borderWidth: type === "bar" ? 1 : 2,
        borderRadius: type === "bar" ? 4 : 0,
      })),
    },
    options: type === "bar" ? defaultBarOptions : defaultLineOptions,
  });
}
