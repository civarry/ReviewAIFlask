// Function to update progress steps
function updateProgressSteps(currentStep) {
    const steps = document.querySelectorAll('.step');
    
    steps.forEach((step, index) => {
        if (index < currentStep) {
            step.classList.remove('active');
            step.classList.add('completed');
        } else if (index === currentStep) {
            step.classList.add('active');
            step.classList.remove('completed');
        } else {
            step.classList.remove('active', 'completed');
        }
    });
}

// Update progress immediately on page load
document.addEventListener('DOMContentLoaded', () => {
    const currentStep = {{ current_step|default(0) }};
    updateProgressSteps(currentStep);
});
