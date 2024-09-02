document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const navbar = document.getElementsByClassName('navbar');
    const content = document.getElementsByClassName('content');

    // Event listener for sidebar toggle
    sidebarToggle.addEventListener('click', () => {
        const isCollapsed = sidebar.classList.toggle('collapsed');
        // toggle navbar shifted
        navbar[0].classList.toggle('shifted');
        content[0].classList.toggle('shifted');
    });
    
    // use /stats endpoint with args start_date and end_date from the date inputs to get the sidebar content. arrange the 4 fields in {'mean_impact': mean_impact, 'median_impact': median_impact, 'max_impact': max_impact, 'min_impact': min_impact} in a 2x2 grid
    const statsUrl = '/stats';
    const mapUrl = '/map';
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const startDateInput = dateInputs[0];
    const endDateInput = dateInputs[1];

    // Function to update the stats and map
    const updateStatsAndMap = async () => {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        const statsUrlWithParams = `${statsUrl}?start_date=${startDate}&end_date=${endDate}`;

        try {
            const response = await fetch(statsUrlWithParams);
            const data = await response.json();
            const summary = document.getElementsByClassName('summary')[0];
            summary.innerHTML = `
            <div class="grid-item"><p data-value="${data.mean_impact}">Mean</p></div>
            <div class="grid-item"><p data-value="${data.median_impact}">Median</p></div>
            <div class="grid-item"><p data-value="${data.max_impact}">Max</p></div>
            <div class="grid-item"><p data-value="${data.min_impact}">Min</p></div><br>
        `;
        } catch (error) {
            console.error('Error fetching stats:', error);
        }

        // Update the map for current tab
        const currentTab = document.querySelector('.navbar a.active');
        const tabName = currentTab.getAttribute('data-tab');
        const selectedOptions = Array.from(document.querySelectorAll(`#options-${tabName} input[type="checkbox"]`)).filter(cb => cb.checked).map(cb => cb.value);
        const mapUrlWithParams = `${mapUrl}?tab=${tabName}&options=${selectedOptions.join(',')}&start_date=${startDate}&end_date=${endDate}`;
        try {
            const response = await fetch(mapUrlWithParams);
            const mapData = await response.json();
            const mapElement = document.getElementById(`map-${tabName}`);
            mapElement.src = mapData.plot_url;
        }
        catch (error) {
            console.error('Error fetching map data:', error);
        }
    };

    // Event listener for date input changes
    dateInputs.forEach(dateInput => {
        dateInput.addEventListener('change', updateStatsAndMap);
    });

    // Event listener for tab clicks
    document.querySelectorAll('.navbar a').forEach(tab => {
        tab.addEventListener('click', async event => {
            event.preventDefault();
            const tabName = event.target.getAttribute('data-tab');
            // add active class to the clicked tab and remove it from the others
            document.querySelectorAll('.navbar a').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            await loadTabContent(tabName, optionsUrl, mapUrl);
        });
    });

    // Event listener for slider input changes
    const slider = document.getElementById('slider');
    // change the text of submit button to 'Display top n incidents' where n is the value of the slider
    const submitButton = document.getElementById('submit');
    slider.addEventListener('input', () => {
        submitButton.textContent = `Display top ${slider.value} incidents`;
    }
    );

    // Event listener for submit button. goes to /get_incidents endpoint with args n from slider, makes a modal with the df returned
    submitButton.addEventListener('click', async () => {
        const n = slider.value;
        const dateInputs = document.querySelectorAll('input[type="date"]');
        const StartDate = dateInputs[0].value;
        const EndDate = dateInputs[1].value;
        const url = `/get_incidents?n=${n}&start_date=${StartDate}&end_date=${EndDate}`;
        try {
            const response = await fetch(url);
            const data = await response.json();
            const newWindow = window.open('', '_blank', 'width=800,height=600');
            console.log(data);
            newWindow.document.write(`
                <html>
                <head>
                    <title>Top Incidents</title>
                    <style>
                    /* Dark theme for the modal */
                    body {
                        background-color: #333;
                        color: #fff;
                    }
                    table {
                        border-collapse: collapse;
                        width: 100%;
                    }
                    th, td {
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }
                    th {
                        background-color: #333;
                        color: #fff;
                    }
                    tr:nth-child(even) {
                        background-color: #444;
                    }
                    tr:hover {
                        background-color: #ddd;
                        color: #000;
                    }
                    </style>
                </head>
                <body>
                    <h2>Top Incidents</h2>
                    <table>
                        <tr>
                            <th>Date</th>
                            <th>State</th>
                            <th>Sector</th>
                            <th>Impact</th>
                            <th>Attack Type</th>
                        </tr>
                        ${data.map(row => `
                            <tr>
                                <td>${row.Date}</td>
                                <td>${row.State}</td>
                                <td>${row.Sector}</td>
                                <td>${row.Impact}</td>
                                <td>${row.Attack_Type}</td>
                            </tr>
                        `).join('')}
                    </table>
                </body>
                </html>
            `);
        } catch (error) {
            console.error('Error fetching incidents:', error);
        }
    });

    // Event listener for modal close button
    const modal = document.getElementById('modal');
    window.addEventListener('click', event => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Load the default tab
    const defaultTab = document.querySelector('.navbar a');
    if (defaultTab) {
        defaultTab.click();
    }
});

function loadTabContent(tabName, optionsUrl, mapUrl) {
    const tabContentDiv = document.getElementById('tab-content');
    tabContentDiv.innerHTML = '<p>Loading...</p>'; // Show loading message
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const StartDate = dateInputs[0].value;
    const EndDate = dateInputs[1].value;
    fetch(`${optionsUrl}?tab=${tabName}`)
        .then(response => response.json())
        .then(data => {
            let content = `
                <u><h4>Drill-down view by ${tabName.replace('_', ' ')}:-</h4></u>
                <div class="container">
                    <div class="checkbox-group-container">
                        <div class="checkbox-group" id="options-${tabName}"></div>
                        <div class="button-group">
                            <button id="select-all-${tabName}" class="select-button">Select All</button>
                            <button id="clear-all-${tabName}" class="clear-button">Clear All</button>
                        </div>
                    </div>
                </div>
                <div class="container map-container">
                    <img id="map-${tabName}" src="">
                </div>
            `;
            tabContentDiv.innerHTML = content;

            const options = data.options;
            const checkboxGroup = document.getElementById(`options-${tabName}`);
            options.forEach(option => {
                const label = document.createElement('label');
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = option;
                label.appendChild(checkbox);
                label.appendChild(document.createTextNode(option));
                checkboxGroup.appendChild(label);
                checkbox.checked = true;
            });

            const checkboxes = document.querySelectorAll(`#options-${tabName} input[type="checkbox"]`);
            const selectedOptions = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
            const mapContainer = document.querySelector('.map-container');
            mapContainer.classList.add('loading');
            return fetch(`${mapUrl}?tab=${tabName}&options=${selectedOptions.join(',')}&start_date=${StartDate}&end_date=${EndDate}`);
        })
        .then(mapResponse => mapResponse.json())
        .then(mapData => {
            const mapElement = document.getElementById(`map-${tabName}`);
            if (mapElement) {
            const mapContainer = document.querySelector('.map-container');
            mapElement.src = mapData.plot_url;
            mapContainer.classList.remove('loading');
            attachCheckboxListeners(tabName, mapUrl);
            }
            else {
                console.log('loading class added');
            }
        })
        .catch(error => {
            console.error('Error loading tab content:', error);
        }).then(() => {
            const dateInputs = document.querySelectorAll('input[type="date"]');
            const StartDate = dateInputs[0].value;
            const EndDate = dateInputs[1].value;
            const statsUrl = '/stats';
            const mapUrl = '/map';
            const updateStatsAndMap = async () => {
                const startDate = StartDate;
                const endDate = EndDate;
                const statsUrlWithParams = `${statsUrl}?start_date=${startDate}&end_date=${endDate}`;
        
                try {
                    const response = await fetch(statsUrlWithParams);
                    const data = await response.json();
                    const summary = document.getElementsByClassName('summary')[0];
                    summary.innerHTML = `
                    <div class="grid-item"><p data-value="${data.mean_impact}">Mean</p></div>
                    <div class="grid-item"><p data-value="${data.median_impact}">Median</p></div>
                    <div class="grid-item"><p data-value="${data.max_impact}">Max</p></div>
                    <div class="grid-item"><p data-value="${data.min_impact}">Min</p></div><br>
                `;
                } catch (error) {
                    console.error('Error fetching stats:', error);
                }
        
                // Update the map for current tab
                const currentTab = document.querySelector('.navbar a.active');
                const tabName = currentTab.getAttribute('data-tab');
                const selectedOptions = Array.from(document.querySelectorAll(`#options-${tabName} input[type="checkbox"]`)).filter(cb => cb.checked).map(cb => cb.value);
                const mapUrlWithParams = `${mapUrl}?tab=${tabName}&options=${selectedOptions.join(',')}&start_date=${startDate}&end_date=${endDate}`;
                try {
                    const response = await fetch(mapUrlWithParams);
                    const mapData = await response.json();
                    const mapElement = document.getElementById(`map-${tabName}`);
                    mapElement.src = mapData.plot_url;
                }
                catch (error) {
                    console.error('Error fetching map data:', error);
                }
            };
            updateStatsAndMap();
        });
}


function attachCheckboxListeners(tabName) {
    const checkboxes = document.querySelectorAll(`#options-${tabName} input[type="checkbox"]`);
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async () => {
            const selectedOptions = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
            const dateInputs = document.querySelectorAll('input[type="date"]');
            const StartDate = dateInputs[0].value;
            const EndDate = dateInputs[1].value;
            const url = `${mapUrl}?tab=${tabName}&options=${selectedOptions.join(',')}&start_date=${StartDate}&end_date=${EndDate}`;
            try {
                const response = await fetch(url);
                const map_data = await response.json();
                const mapElement = document.getElementById(`map-${tabName}`);
                if (mapElement) mapElement.src = map_data.plot_url;
            } catch (error) {
                console.error('Error fetching map data:', error);
            }
        });
    });

    document.getElementById(`select-all-${tabName}`).addEventListener('click', () => {
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
        const selectedOptions = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
        const dateInputs = document.querySelectorAll('input[type="date"]');
        const StartDate = dateInputs[0].value;
        const EndDate = dateInputs[1].value;
        const url = `${mapUrl}?tab=${tabName}&options=${selectedOptions.join(',')}&start_date=${StartDate}&end_date=${EndDate}`;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                const mapElement = document.getElementById(`map-${tabName}`);
                mapElement.src = data.plot_url;
            });
    });

    document.getElementById(`clear-all-${tabName}`).addEventListener('click', () => {
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        const selectedOptions = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
        const dateInputs = document.querySelectorAll('input[type="date"]');
        const StartDate = dateInputs[0].value;
        const EndDate = dateInputs[1].value;
        const url = `${mapUrl}?tab=${tabName}&options=${selectedOptions.join(',')}&start_date=${StartDate}&end_date=${EndDate}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                const mapElement = document.getElementById(`map-${tabName}`);
                mapElement.src = data.plot_url;
            });
    });
}