/* JavaScript Unique Optimisé - Lobiko Health */
/* Fichier consolidé sans redondances */

// Utilitaires communs
function validateField(field) {
    const value = field.value.trim();
    const isRequired = field.hasAttribute('required');

    if (isRequired && !value) {
        field.classList.add('field-error');
        field.classList.remove('field-valid');
        return false;
    } else {
        let isValid = true;
        if (field.type === 'email') {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            isValid = emailRegex.test(value);
        } else if (field.type === 'tel') {
            const phoneRegex = /^[\d\s\-\+\(\)]+$/;
            isValid = phoneRegex.test(value) && value.length >= 8;
        }

        if (isValid) {
            field.classList.add('field-valid');
            field.classList.remove('field-error');
            return true;
        } else {
            field.classList.add('field-error');
            field.classList.remove('field-valid');
            return false;
        }
    }
}

// Gestion des messages système
function handleSystemMessages() {
    const messages = document.querySelectorAll('.messages li');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
}

// Animation des icônes d'input
function setupInputIconAnimations(inputs) {
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            const icon = this.parentNode.querySelector('.input-icon');
            if (icon) {
                icon.style.transform = 'scale(1.1)';
                icon.style.color = 'var(--primary-blue)';
            }
        });

        input.addEventListener('blur', function() {
            if (!this.value) {
                const icon = this.parentNode.querySelector('.input-icon');
                if (icon) {
                    icon.style.transform = 'scale(1)';
                    icon.style.color = 'var(--medium-gray)';
                }
            }
        });
    });
}

// Validation en temps réel des formulaires
function setupFormValidation(form) {
    const inputs = form.querySelectorAll('input, select, textarea');

    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });

        input.addEventListener('input', function() {
            if (this.classList.contains('field-error')) {
                validateField(this);
            }
        });
    });

    return inputs;
}

// Animation de soumission des formulaires
function setupFormSubmission(form, buttonText = 'Chargement...') {
    form.addEventListener('submit', function() {
        const submitBtn = form.querySelector('.btn-primary');
        if (submitBtn) {
            submitBtn.classList.add('loading');
            if (buttonText.includes('Connexion')) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 0.5rem;"></i>' + buttonText;
            } else {
                submitBtn.textContent = buttonText;
            }
        }
    });
}

// === FONCTIONS SPÉCIFIQUES AU DASHBOARD ===

// Navigation entre sections
function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active class from all menu items
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(sectionId).classList.add('active');
    
    // Add active class to clicked menu item
    event.target.classList.add('active');
}

// Toggle sidebar mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

// Filtrer les consultations
function filterConsultations(filter) {
    // Update button states
    document.querySelectorAll('#consultations .btn').forEach(btn => {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-outline');
    });
    event.target.classList.remove('btn-outline');
    event.target.classList.add('btn-primary');
    
    // Filter logic would go here
    console.log('Filtering consultations by:', filter);
}

// Fermer la sidebar en cliquant à l'extérieur (mobile)
function setupSidebarClickOutside() {
    document.addEventListener('click', function(event) {
        const sidebar = document.getElementById('sidebar');
        const menuToggle = document.querySelector('.menu-toggle');
        
        if (sidebar && menuToggle && window.innerWidth <= 768 && 
            !sidebar.contains(event.target) && 
            !menuToggle.contains(event.target)) {
            sidebar.classList.remove('open');
        }
    });
}

// Effet de parallaxe sur le header
function setupParallaxEffect() {
    window.addEventListener('scroll', function() {
        const header = document.querySelector('.header');
        if (header && !header.classList.contains('dashboard-header')) {
            const scrolled = window.pageYOffset;
            header.style.transform = `translateY(${scrolled * 0.5}px)`;
        }
    });
}

// Animation des cartes statistiques
function setupStatsCardAnimation() {
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
}

// === INITIALISATION SELON LA PAGE ===

document.addEventListener('DOMContentLoaded', function() {
    // Détection de la page actuelle
    const isLoginPage = document.getElementById('loginForm');
    const isInscriptionPage = document.getElementById('inscriptionForm');
    const isDashboardPage = document.querySelector('.sidebar');

    // Gestion commune des messages
    handleSystemMessages();

    // === PAGE DE CONNEXION ===
    if (isLoginPage) {
        const inputs = setupFormValidation(isLoginPage);
        setupInputIconAnimations(inputs);
        setupFormSubmission(isLoginPage, 'Connexion en cours...');
        setupParallaxEffect();
    }

    // === PAGE D'INSCRIPTION ===
    if (isInscriptionPage) {
        // Initialisation Select2 si jQuery est disponible
        if (typeof $ !== 'undefined') {
            $('.select2').select2({
                placeholder: "Choisissez les langues",
                width: '100%'
            });
        }

        setupFormValidation(isInscriptionPage);
        setupFormSubmission(isInscriptionPage, 'Inscription en cours...');
    }

    // === PAGE DASHBOARD ===
    if (isDashboardPage) {
        setupSidebarClickOutside();
        setupStatsCardAnimation();
    }

    // Initialisation générale pour toutes les pages
    console.log('Lobiko Health - JavaScript initialisé');
});

// Exposition des fonctions globales nécessaires
window.showSection = showSection;
window.toggleSidebar = toggleSidebar;
window.filterConsultations = filterConsultations;

