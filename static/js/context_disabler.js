// Disable right-click context menu
document.addEventListener('contextmenu', function (e) {
    e.preventDefault();
    $('#noAccessModal').modal('show'); // Show the Bootstrap modal
});

// Disable keyboard shortcuts for developer tools
document.addEventListener('keydown', function (e) {
    // Disable F12, Ctrl+Shift+I, Ctrl+U, Ctrl+Shift+C
    if (e.key === 'F12' || 
        (e.ctrlKey && (e.shiftKey && e.key === 'I')) || 
        (e.ctrlKey && e.key === 'U') || 
        (e.ctrlKey && (e.shiftKey && e.key === 'C'))) {
        e.preventDefault();
        $('#noAccessModal').modal('show'); // Show the Bootstrap modal
    }

    if (e.ctrlKey && e.key.toLowerCase() === 'u') {
        e.preventDefault();
        $('#noAccessModal').modal('show'); // Show the Bootstrap modal
    }
});