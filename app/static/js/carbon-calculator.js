document.addEventListener('DOMContentLoaded', function() {
    try {
        const calculator = document.getElementById('carbonCalculator');
        const results = document.getElementById('results');

        if (!calculator) {
            console.error('Carbon calculator form not found');
            return;
        }

        if (!results) {
            console.error('Results container not found');
            return;
        }

        // CO2 emission factors (grams per km)
        const emissionFactors = {
            petrol: 120,
            diesel: 130,
            hybrid: 80,
            electric: 40
        };

        // Average CO2 absorption by a tree per year (kg)
        const TREE_CO2_ABSORPTION = 22;

        calculator.addEventListener('submit', function(e) {
            e.preventDefault();
            try {
                // Get form values
                const distance = parseFloat(document.getElementById('distance').value);
                const days = parseInt(document.getElementById('days').value);
                const carType = document.getElementById('carType').value;
                const weeks = parseInt(document.getElementById('weeks').value);

                if (isNaN(distance) || isNaN(days) || isNaN(weeks)) {
                    throw new Error('Invalid input values');
                }

                // Calculate annual CO2 emissions
                const dailyEmissions = (distance * emissionFactors[carType]) / 1000; // Convert to kg
                const annualEmissions = dailyEmissions * days * weeks;

                // Calculate equivalent trees
                const treesEquivalent = Math.round(annualEmissions / TREE_CO2_ABSORPTION);

                // Update results
                document.getElementById('co2Savings').textContent = Math.round(annualEmissions);
                document.getElementById('treesEquivalent').textContent = treesEquivalent;

                // Show results
                results.style.display = 'block';
            } catch (error) {
                console.error('Error calculating carbon savings:', error);
                alert('There was an error calculating your carbon savings. Please check your input values.');
            }
        });
    } catch (error) {
        console.error('Error initializing carbon calculator:', error);
    }
}); 