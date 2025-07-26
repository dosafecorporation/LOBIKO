/* JavaScript Unique Optimisé - Lobiko Health */
/* Fichier consolidé sans redondances */

// Utilitaires communs
function validateField(field) {
    if (!field) return false;
    
    const value = field.value ? field.value.trim() : '';
    const isRequired = field.hasAttribute('required') || field.classList.contains('required');

    if (isRequired && !value) {
        field.classList.add('field-error', 'error');
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
            field.classList.remove('field-error', 'error');
            return true;
        } else {
            field.classList.add('field-error', 'error');
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



// === FONCTIONS SPÉCIFIQUES AU WIZARD D'INSCRIPTION ===

// Variables globales pour le wizard
let currentStep = 1;
const totalSteps = 4;

// Navigation du wizard
function nextStep() {
    if (validateCurrentStep()) {
        if (currentStep < totalSteps) {
            currentStep++;
            updateWizardDisplay();
        }
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        updateWizardDisplay();
    }
}

// Validation de l'étape actuelle
function validateCurrentStep() {
    const currentStepElement = document.querySelector(`.wizard-step[data-step="${currentStep}"]`);
    if (!currentStepElement) return false;
    
    const requiredFields = currentStepElement.querySelectorAll('input[required], select[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    // Validation spécifique pour l'étape 4 (mots de passe)
    if (currentStep === 4) {
        const password = document.getElementById('id_password');
        const confirmPassword = document.getElementById('id_confirm_password');
        
        if (password && confirmPassword && password.value !== confirmPassword.value) {
            confirmPassword.classList.add('field-error');
            showFieldError(confirmPassword, 'Les mots de passe ne correspondent pas');
            isValid = false;
        }
    }
    
    return isValid;
}

// Mise à jour de l'affichage du wizard
function updateWizardDisplay() {
    // Masquer toutes les étapes
    document.querySelectorAll('.wizard-step').forEach(step => {
        step.classList.remove('active');
    });
    
    // Afficher l'étape actuelle
    const currentStepElement = document.querySelector(`.wizard-step[data-step="${currentStep}"]`);
    if (currentStepElement) {
        currentStepElement.classList.add('active');
    }
    
    // Mettre à jour les indicateurs de progression
    document.querySelectorAll('.step').forEach((step, index) => {
        const stepNumber = index + 1;
        step.classList.remove('active', 'completed');
        
        if (stepNumber === currentStep) {
            step.classList.add('active');
        } else if (stepNumber < currentStep) {
            step.classList.add('completed');
        }
    });
    
    // Mettre à jour la barre de progression
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
        const progressPercentage = (currentStep / totalSteps) * 100;
        progressFill.style.width = `${progressPercentage}%`;
    }
    
    // Gérer l'affichage des boutons
    const prevBtn = document.querySelector('.wizard-prev');
    const nextBtn = document.querySelector('.wizard-next');
    const submitBtn = document.querySelector('.wizard-submit');
    
    if (prevBtn) {
        prevBtn.style.display = currentStep === 1 ? 'none' : 'inline-flex';
    }
    
    if (nextBtn && submitBtn) {
        if (currentStep === totalSteps) {
            nextBtn.style.display = 'none';
            submitBtn.style.display = 'inline-flex';
        } else {
            nextBtn.style.display = 'inline-flex';
            submitBtn.style.display = 'none';
        }
    }
}

// Afficher une erreur sur un champ
function showFieldError(field, message) {
    // Supprimer les anciens messages d'erreur
    const existingError = field.parentNode.querySelector('.field-error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Créer le nouveau message d'erreur
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error-message';
    errorElement.textContent = message;
    errorElement.style.color = 'var(--error-red)';
    errorElement.style.fontSize = 'var(--font-size-sm)';
    errorElement.style.marginTop = 'var(--spacing-xs)';
    
    field.parentNode.appendChild(errorElement);
}

// Initialisation du wizard
function initializeWizard() {
    const wizardForm = document.getElementById('inscriptionWizardForm');
    if (!wizardForm) {
        console.log('Formulaire wizard non trouvé');
        return;
    }
    
    console.log('Initialisation du wizard...');
    
    // Événements des boutons
    const nextBtn = document.querySelector('.wizard-next');
    const prevBtn = document.querySelector('.wizard-prev');
    
    if (nextBtn) {
        nextBtn.addEventListener('click', function(e) {
            e.preventDefault();
            nextStep();
        });
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', function(e) {
            e.preventDefault();
            prevStep();
        });
    }
    
    // Validation en temps réel
    const allInputs = wizardForm.querySelectorAll('input, select, textarea');
    allInputs.forEach(input => {
        if (input.addEventListener) {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('field-error') || this.classList.contains('error')) {
                    validateField(this);
                }
                
                // Supprimer les messages d'erreur personnalisés
                const errorMessage = this.parentNode.querySelector('.field-error-message');
                if (errorMessage) {
                    errorMessage.remove();
                }
            });
        }
    });
    
    // Navigation par clavier
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            const activeElement = document.activeElement;
            if (activeElement && activeElement.tagName !== 'TEXTAREA' && activeElement.type !== 'submit') {
                e.preventDefault();
                if (currentStep < totalSteps) {
                    nextStep();
                }
            }
        }
    });
    
    // Initialiser l'affichage
    updateWizardDisplay();
    console.log('Wizard initialisé avec succès');
}

// === FONCTIONS SPÉCIFIQUES À LA DISCUSSION ===

// Variables globales pour la discussion
let discussionSocket = null;
let sessionId = null;

// Initialisation de la discussion
function initializeDiscussion() {
    const discussionContainer = document.querySelector('.discussion-container');
    if (!discussionContainer) return;
    
    // Récupérer l'ID de session depuis le DOM ou les données
    const sessionElement = document.querySelector('[data-session-id]');
    if (sessionElement) {
        sessionId = sessionElement.dataset.sessionId;
    }
    
    // Auto-scroll du chat
    scrollChatToBottom();
    
    // Focus sur le champ de message
    const messageTextarea = document.querySelector('textarea[name="message"]');
    if (messageTextarea) {
        messageTextarea.focus();
        setupAutoResize(messageTextarea);
    }
    
    // Initialiser WebSocket si disponible
    if (sessionId) {
        initializeWebSocket();
    }
    
    // Gestion du formulaire de message
    setupMessageForm();
    
    // Gestion des médias
    setupMediaHandlers();
}

// Auto-scroll du chat vers le bas
function scrollChatToBottom() {
    const chatContainer = document.getElementById('chatContainer');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Redimensionnement automatique du textarea
function setupAutoResize(textarea) {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
}

// Initialisation WebSocket
function initializeWebSocket() {
    try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/discussion/${sessionId}/`;
        
        discussionSocket = new WebSocket(wsUrl);
        
        discussionSocket.onopen = function(e) {
            console.log('WebSocket connecté avec succès');
        };
        
        discussionSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            
            if (data.type === 'new_message') {
                addNewMessage(data.data);
            } else if (data.type === 'new_media') {
                addNewMedia(data.data);
            }
        };
        
        discussionSocket.onerror = function(error) {
            console.error('WebSocket Error:', error);
        };
        
        discussionSocket.onclose = function(e) {
            console.log('WebSocket fermé');
            // Tentative de reconnexion après 3 secondes
            setTimeout(() => {
                if (sessionId) {
                    initializeWebSocket();
                }
            }, 3000);
        };
    } catch (error) {
        console.error('Erreur de connexion WebSocket:', error);
    }
}

// Configuration du formulaire de message
function setupMessageForm() {
    const messageForm = document.getElementById('messageForm');
    if (!messageForm) return;
    
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const messageInput = this.querySelector('textarea[name="message"]');
        const messageContent = messageInput.value.trim();
        
        if (!messageContent) return;
        
        // Désactiver le bouton d'envoi temporairement
        const sendBtn = this.querySelector('.send-btn');
        if (sendBtn) {
            sendBtn.disabled = true;
        }
        
        // Envoyer le message via AJAX
        fetch(this.action || window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Ajouter le message à l'interface si pas de WebSocket
                if (!discussionSocket || discussionSocket.readyState !== WebSocket.OPEN) {
                    addNewMessage({
                        id: data.message_id,
                        content: messageContent,
                        sender: 'medecin',
                        timestamp: data.timestamp,
                        type: 'text'
                    });
                }
                
                // Vider le champ et remettre le focus
                messageInput.value = '';
                messageInput.style.height = 'auto';
                messageInput.focus();
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            alert('Erreur lors de l\'envoi du message');
        })
        .finally(() => {
            if (sendBtn) {
                sendBtn.disabled = false;
            }
        });
    });
}

// Ajouter un nouveau message à l'interface
function addNewMessage(data) {
    const chatContainer = document.getElementById('chatContainer');
    if (!chatContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-wrapper ${data.sender === 'medecin' ? 'message-sent' : 'message-received'}`;
    
    const timestamp = new Date(data.timestamp);
    const timeString = timestamp.toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'});
    
    messageDiv.innerHTML = `
        <div class="message-bubble">
            <div class="message-header">
                <span class="sender-name">
                    <i class="fas ${data.sender === 'medecin' ? 'fa-user-md' : 'fa-user'}"></i>
                    ${data.sender === 'medecin' ? 'Vous' : 'Patient'}
                </span>
                <span class="message-time">${timeString}</span>
            </div>
            <div class="message-content">
                <div class="text-content">
                    ${data.content.replace(/\n/g, '<br>')}
                </div>
            </div>
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    scrollChatToBottom();
}

// Ajouter un nouveau média à l'interface
function addNewMedia(data) {
    const chatContainer = document.getElementById('chatContainer');
    if (!chatContainer) return;
    
    let mediaContent = '';
    
    switch (data.type) {
        case 'image':
            mediaContent = `
                <div class="media-container image-media">
                    <img src="${data.url}" alt="Media envoyé" class="media-image">
                    <div class="media-actions">
                        <a href="${data.url}" target="_blank" class="media-btn">
                            <i class="fas fa-expand"></i>
                        </a>
                        <a href="/medecins/download/${sessionId}/${data.id}/" class="media-btn">
                            <i class="fas fa-download"></i>
                        </a>
                    </div>
                </div>
            `;
            break;
        case 'audio':
            mediaContent = `
                <div class="media-container audio-media">
                    <div class="audio-player">
                        <audio controls>
                            <source src="${data.url}" type="${data.mime_type}">
                            Votre navigateur ne supporte pas l'élément audio.
                        </audio>
                    </div>
                    <div class="media-actions">
                        <a href="/medecins/download/${sessionId}/${data.id}/" class="media-btn">
                            <i class="fas fa-download"></i>
                        </a>
                    </div>
                </div>
            `;
            break;
        case 'video':
            mediaContent = `
                <div class="media-container video-media">
                    <video controls class="media-video">
                        <source src="${data.url}" type="${data.mime_type}">
                        Votre navigateur ne supporte pas l'élément vidéo.
                    </video>
                    <div class="media-actions">
                        <a href="/medecins/download/${sessionId}/${data.id}/" class="media-btn">
                            <i class="fas fa-download"></i>
                        </a>
                    </div>
                </div>
            `;
            break;
        default:
            mediaContent = `
                <div class="media-container file-media">
                    <div class="file-icon">
                        <i class="fas fa-file"></i>
                    </div>
                    <div class="file-info">
                        <span class="file-name">${data.name}</span>
                    </div>
                    <div class="media-actions">
                        <a href="/medecins/download/${sessionId}/${data.id}/" class="media-btn">
                            <i class="fas fa-download"></i>
                        </a>
                    </div>
                </div>
            `;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-wrapper ${data.sender === 'medecin' ? 'message-sent' : 'message-received'}`;
    
    const timestamp = new Date(data.timestamp);
    const timeString = timestamp.toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'});
    
    messageDiv.innerHTML = `
        <div class="message-bubble">
            <div class="message-header">
                <span class="sender-name">
                    <i class="fas ${data.sender === 'medecin' ? 'fa-user-md' : 'fa-user'}"></i>
                    ${data.sender === 'medecin' ? 'Vous' : 'Patient'}
                </span>
                <span class="message-time">${timeString}</span>
            </div>
            <div class="message-content">
                ${mediaContent}
            </div>
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    scrollChatToBottom();
}

// Configuration des gestionnaires de médias
function setupMediaHandlers() {
    // Gestion du menu d'attachement
    const attachmentBtn = document.querySelector('.attachment-btn');
    const attachmentMenu = document.getElementById('attachmentMenu');
    
    if (attachmentBtn && attachmentMenu) {
        attachmentBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleAttachmentMenu();
        });
        
        // Fermer le menu en cliquant ailleurs
        document.addEventListener('click', function(e) {
            if (!attachmentMenu.contains(e.target) && !attachmentBtn.contains(e.target)) {
                attachmentMenu.style.display = 'none';
            }
        });
    }
}

// Basculer le menu d'attachement
function toggleAttachmentMenu() {
    const menu = document.getElementById('attachmentMenu');
    if (menu) {
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }
}

// Déclencher la sélection de fichier
function triggerFileInput(type) {
    const input = document.getElementById(type + 'Input');
    if (input) {
        input.click();
    }
    toggleAttachmentMenu();
}

// Gérer la sélection de fichier
function handleFileSelect(input, type) {
    const file = input.files[0];
    if (file) {
        console.log('Fichier sélectionné:', file.name, 'Type:', type);
        // Ici vous pouvez ajouter la logique d'upload de fichier
        // Réinitialiser l'input
        input.value = '';
    }
}

// Rejoindre un appel Jitsi
function joinJitsiCall(linkPath) {
    const fullLink = linkPath.startsWith('http') ? linkPath : window.location.origin + linkPath;
    const newWindow = window.open(fullLink, '_blank', 'width=1200,height=800');
    
    if (!newWindow || newWindow.closed || typeof newWindow.closed == 'undefined') {
        alert("L'ouverture de la fenêtre a été bloquée. Veuillez autoriser les popups pour ce site.");
        if (confirm("Voulez-vous être redirigé vers l'appel dans cet onglet ?")) {
            window.location.href = fullLink;
        }
    }
}

// === MISE À JOUR DE L'INITIALISATION PRINCIPALE ===

// Mise à jour de l'initialisation DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // Détection de la page actuelle
    const isLoginPage = document.getElementById('loginForm');
    const isInscriptionPage = document.getElementById('inscriptionForm') || document.getElementById('inscriptionWizardForm');
    const isDashboardPage = document.querySelector('.sidebar');
    const isDiscussionPage = document.querySelector('.discussion-container');

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

        // Initialiser le wizard si c'est la nouvelle version
        if (document.getElementById('inscriptionWizardForm')) {
            initializeWizard();
        } else {
            setupFormValidation(isInscriptionPage);
            setupFormSubmission(isInscriptionPage, 'Inscription en cours...');
        }
    }

    // === PAGE DASHBOARD ===
    if (isDashboardPage) {
        setupSidebarClickOutside();
        setupStatsCardAnimation();
    }

    // === PAGE DISCUSSION ===
    if (isDiscussionPage) {
        initializeDiscussion();
    }

    // Initialisation générale pour toutes les pages
    console.log('Lobiko Health - JavaScript initialisé');
});

// Exposition des nouvelles fonctions globales
window.nextStep = nextStep;
window.prevStep = prevStep;
window.toggleAttachmentMenu = toggleAttachmentMenu;
window.triggerFileInput = triggerFileInput;
window.handleFileSelect = handleFileSelect;
window.joinJitsiCall = joinJitsiCall;

