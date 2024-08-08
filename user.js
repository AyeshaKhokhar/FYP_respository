// Function to show the respective section
function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.form-container, #dashboard-section, #your-hotels-section').forEach(section => {
        section.style.display = 'none';
    });
    // Show the selected section
    document.getElementById(sectionId).style.display = 'block';
}

// Data for the chart (example data)
const ratingData = {
    labels: ['Hotel A', 'Hotel B', 'Hotel C', 'Hotel D','Hotel E', 'Hotel F'],
    datasets: [{
        label: 'Rating Score',
        data: [4.5, 3.7, 4.0, 3.9,2.5,3.0],
        backgroundColor: 'rgba(214, 139, 73, 0.3)',
        borderColor: 'rgba(214, 139, 73, 1)',
        borderWidth: 1
    }]
};

// Configuration for the chart
const config = {
    type: 'bar',
    data: ratingData,
    options: {
        scales: {
            y: {
                beginAtZero: true,
                max: 5
            }
        },
        maintainAspectRatio: false
    }
};

// Render the chart
const ratingGraph = new Chart(
    document.getElementById('rating-graph'),
    config
);

// Initial display setup
showSection('dashboard-section');
