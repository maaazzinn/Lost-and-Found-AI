document.addEventListener('DOMContentLoaded', () => {
    // Fade in elements
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach(element => {
        element.style.opacity = 0;
        setTimeout(() => {
            element.style.transition = 'opacity 0.5s';
            element.style.opacity = 1;
        }, 100);
    });

    // Image preview functionality
    const imageInputs = document.querySelectorAll('input[type="file"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const imagePreview = this.closest('.form-group').querySelector('.image-preview-container img');
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    // Confidence color coding
    const confidenceBadges = document.querySelectorAll('.confidence-badge');
    confidenceBadges.forEach(badge => {
        const confidence = parseInt(badge.dataset.confidence);
        if (confidence > 90) {
            badge.style.backgroundColor = '#2ecc71';  // Green
        } else if (confidence > 75) {
            badge.style.backgroundColor = '#f39c12';  // Orange
        } else {
            badge.style.backgroundColor = '#e74c3c';  // Red
        }
    });

    // Interactive form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const requiredFields = this.querySelectorAll('[required]');
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                    field.addEventListener('input', function() {
                        this.classList.remove('error');
                    });
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });

    // Smooth scroll to sections
    const navLinks = document.querySelectorAll('a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});