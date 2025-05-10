document.addEventListener('DOMContentLoaded', function() {
    console.log('Autocomplete script loaded'); // Debug log

    const searchInput = document.getElementById('address');
    if (!searchInput) {
        console.error('Search input not found!');
        return;
    }

    // Create autocomplete container
    const autocompleteContainer = document.createElement('div');
    autocompleteContainer.id = 'autocompleteResults';
    autocompleteContainer.className = 'autocomplete-results';
    searchInput.parentNode.appendChild(autocompleteContainer);

    // Add input event listener
    searchInput.addEventListener('input', async function() {
        const query = this.value.trim();
        console.log('Searching for:', query); // Debug log

        if (query.length === 0) {
            autocompleteContainer.style.display = 'none';
            return;
        }

        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&countrycodes=be&city=Antwerp&limit=5`
            );
            const data = await response.json();
            console.log('Received results:', data); // Debug log

            // Clear previous results
            autocompleteContainer.innerHTML = '';

            if (data.length === 0) {
                autocompleteContainer.style.display = 'none';
                return;
            }

            // Add new results
            data.forEach(result => {
                const div = document.createElement('div');
                div.className = 'autocomplete-item';
                div.textContent = result.display_name;
                
                div.addEventListener('click', () => {
                    searchInput.value = result.display_name;
                    autocompleteContainer.style.display = 'none';
                    document.getElementById('searchForm').dispatchEvent(new Event('submit'));
                });
                
                autocompleteContainer.appendChild(div);
            });

            autocompleteContainer.style.display = 'block';
        } catch (error) {
            console.error('Error fetching addresses:', error);
        }
    });

    // Close autocomplete when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !autocompleteContainer.contains(e.target)) {
            autocompleteContainer.style.display = 'none';
        }
    });
}); 