function formatDistance(km) {
    if (km === null || km === undefined) return '-';
    return km < 1 ? `${Math.round(km * 1000)}m` : `${km.toFixed(1)}km`;
}

function updateProgressBarColor(score) {
    const progressBar = document.getElementById('scoreBar');
    if (!progressBar) return;
    
    let color;
    if (score >= 8) {
        color = '#28a745';
    } else if (score >= 6) {
        color = '#17a2b8';
    } else if (score >= 4) {
        color = '#ffc107';
    } else if (score >= 2) {
        color = '#fd7e14';
    } else {
        color = '#dc3545';
    }
    
    progressBar.style.backgroundColor = color;
}

function handleFetchError(error) {
    console.error('Error:', error);
    alert('An error occurred. Please try again.');
}

document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl)
        });
    }
    
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    if (popoverTriggerList.length > 0) {
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl)
        });
    }
    
    const addressInput = document.getElementById('address-input');
    if (addressInput) {
        addressInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.getElementById('search-btn').click();
            }
        });
    }
}); 