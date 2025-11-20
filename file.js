// Nite mode toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const toggleButton = document.getElementById('niteToggle');
    const body = document.body;
    
    // Check if user has a saved preference
    const savedMode = localStorage.getItem('niteMode');
    if (savedMode === 'enabled') {
        body.classList.add('nite-mode');
        toggleButton.textContent = 'Toggle Day Mode';
    }
    
    // Toggle nite mode on button click
    toggleButton.addEventListener('click', function() {
        body.classList.toggle('nite-mode');
        
        if (body.classList.contains('nite-mode')) {
            toggleButton.textContent = 'Toggle Day Mode';
            localStorage.setItem('niteMode', 'enabled');
        } else {
            toggleButton.textContent = 'Toggle Nite Mode';
            localStorage.setItem('niteMode', 'disabled');
        }
    });
});
