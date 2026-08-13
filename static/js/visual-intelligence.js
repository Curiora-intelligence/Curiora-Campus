document.addEventListener("DOMContentLoaded", () => {
    /*
    ========================================================
    ELEMENTS
    ========================================================
    */
    const app = document.querySelector('[data-curio-app]');
    if (!app) return;

    const cameraButton = app.querySelector('[data-curio-open-camera]');
    const imageButton = app.querySelector('[data-curio-upload]');
    const videoPauseButton = app.querySelector('[data-curio-pause-video]');
    const microphonePauseButton = app.querySelector('[data-curio-mute-audio]');
    const cancelCameraButtons = app.querySelectorAll('[data-curio-close-camera]');
    const cameraContainer = app.querySelector('[data-curio-camera]');
    const cameraPreview = app.querySelector('[data-curio-video]');
    const imageContainer = app.querySelector('[data-curio-preview-shell]');
    const imagePreview = app.querySelector('[data-curio-preview]');
    const cancelImageButton = app.querySelector('[data-curio-remove-image]');
    const imageInput = app.querySelector('[data-curio-file-input]');
    const menuTrigger = app.querySelector('[data-curio-menu-trigger]');
    const menu = app.querySelector('[data-curio-menu]');
    
    const imageConversation = app.querySelector('[data-curio-conversation]');
    const imageMessageForm = app.querySelector('[data-curio-form]');
    const imageMessageInput = app.querySelector('[data-curio-message]');
    const imageVoiceButton = app.querySelector('[data-curio-mic]');
    const imageSendButton = app.querySelector('[data-curio-send]');
    const imageStatus = app.querySelector('[data-curio-status]');
    const cameraStatus = app.querySelector('[data-curio-camera-status]');
    
    /*
    ========================================================
    MENU TOGGLE
    ========================================================
    */
    if (menuTrigger && menu) {
        menuTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            menu.hidden = !menu.hidden;
        });
        document.addEventListener('click', () => {
            menu.hidden = true;
        });
    }

    /*
    ========================================================
    CAMERA STATE
    ========================================================
    */
    let cameraStream = null;
    let cameraActive = false;
    let videoPaused = false;
    let microphonePaused = false;

    /*
    ========================================================
    IMAGE STATE
    ========================================================
    */
    let selectedImageFile = null;
    let selectedImageObjectUrl = null;

    /*
    ========================================================
    IMAGE VOICE STATE
    ========================================================
    */
    let speechRecognition = null;
    let voiceInputSupported = false;
    let voiceInputActive = false;
    let speechBaseText = "";

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
        voiceInputSupported = true;
        speechRecognition = new SpeechRecognition();
        speechRecognition.continuous = true;
        speechRecognition.interimResults = true;
        speechRecognition.lang = document.documentElement.lang || "en-US";
    } else {
        if (imageVoiceButton) {
            imageVoiceButton.disabled = true;
            imageVoiceButton.setAttribute("aria-label", "Voice input is not supported in this browser");
        }
    }

    /*
    ========================================================
    UI STATE
    ========================================================
    */
    function setIdleState() {
        stopImageVoiceInput();

        cameraActive = false;
        videoPaused = false;
        microphonePaused = false;

        if (cameraContainer) {
            cameraContainer.classList.add('is-hidden');
            setTimeout(() => {
                if (!cameraActive) cameraContainer.hidden = true;
            }, 400); // match transition
        }
        if (imageContainer) {
            imageContainer.classList.add('is-hidden');
            setTimeout(() => {
                if (!selectedImageFile) imageContainer.hidden = true;
            }, 400);
        }
        if (imageConversation) imageConversation.hidden = true;
        if (imageStatus) imageStatus.textContent = "Curio is ready";
        
        if (videoPauseButton) videoPauseButton.textContent = "Pause video";
        if (microphonePauseButton) microphonePauseButton.textContent = "Mute audio";

        if (imageVoiceButton) {
            imageVoiceButton.classList.remove("is-listening");
            imageVoiceButton.setAttribute("aria-pressed", "false");
        }
        
        app.classList.remove("camera-active", "camera-paused");
    }

    function setCameraState() {
        if (cameraContainer) {
            cameraContainer.hidden = false;
            // Force reflow
            void cameraContainer.offsetWidth;
            cameraContainer.classList.remove('is-hidden');
        }
        if (imageContainer) {
            imageContainer.classList.add('is-hidden');
            setTimeout(() => {
                if (!selectedImageFile && cameraActive) imageContainer.hidden = true;
            }, 400);
        }
        if (imageConversation) imageConversation.hidden = true;

        if (cameraStatus) cameraStatus.textContent = "Curio is observing";
        
        app.classList.add("camera-active");
    }

    function setImageState() {
        if (cameraContainer) {
            cameraContainer.classList.add('is-hidden');
            setTimeout(() => {
                if (!cameraActive) cameraContainer.hidden = true;
            }, 400);
        }
        if (imageContainer) {
            imageContainer.hidden = false;
            // Force reflow
            void imageContainer.offsetWidth;
            imageContainer.classList.remove('is-hidden');
        }
        if (imageConversation) imageConversation.hidden = false;

        if (imageStatus) imageStatus.textContent = "Curio is ready to examine this image";
        if (imageContainer) imageContainer.classList.add("image-active");

        requestAnimationFrame(() => {
            if (imageMessageInput) imageMessageInput.focus();
        });
    }

    /*
    ========================================================
    IMAGE INPUT
    ========================================================
    */
    if (imageButton && imageInput) {
        imageButton.addEventListener("click", () => {
            if (cameraActive) return;
            imageInput.click();
        });
    }

    if (imageInput) {
        imageInput.addEventListener("change", () => {
            const file = imageInput.files?.[0];
            if (!file) return;

            if (!file.type.startsWith("image/")) {
                console.error("Curiora: selected file is not an image.");
                imageInput.value = "";
                return;
            }

            if (selectedImageObjectUrl) {
                URL.revokeObjectURL(selectedImageObjectUrl);
            }

            selectedImageFile = file;
            selectedImageObjectUrl = URL.createObjectURL(file);

            if (imagePreview) {
                imagePreview.src = selectedImageObjectUrl;
                imagePreview.alt = `Selected image: ${file.name}`;
            }

            if (imageConversation) imageConversation.replaceChildren();
            if (imageMessageInput) {
                imageMessageInput.value = "";
                imageMessageInput.style.height = "auto";
            }

            setImageState();
        });
    }

    /*
    ========================================================
    CANCEL IMAGE
    ========================================================
    */
    function cancelImage() {
        stopImageVoiceInput();

        selectedImageFile = null;

        if (selectedImageObjectUrl) {
            URL.revokeObjectURL(selectedImageObjectUrl);
            selectedImageObjectUrl = null;
        }

        if (imagePreview) {
            imagePreview.removeAttribute("src");
            imagePreview.alt = "Selected image for Curio analysis";
        }

        if (imageInput) imageInput.value = "";
        if (imageMessageInput) {
            imageMessageInput.value = "";
            imageMessageInput.style.height = "auto";
        }

        if (imageConversation) imageConversation.replaceChildren();
        if (imageContainer) imageContainer.classList.remove("image-active");

        setIdleState();
    }

    if (cancelImageButton) {
        cancelImageButton.addEventListener("click", cancelImage);
    }

    /*
    ========================================================
    IMAGE CONVERSATION
    ========================================================
    */
    function addConversationMessage(role, message, imageUrl = null) {
        if (!imageConversation) return;

        const messageElement = document.createElement("article");
        
        if (role === 'curio') {
            messageElement.className = "curio-message curio-message--assistant";
            
            const avatar = document.createElement("span");
            avatar.className = "curio-message-avatar";
            avatar.setAttribute("aria-hidden", "true");
            avatar.textContent = "C";
            
            const div = document.createElement("div");
            const p = document.createElement("p");
            p.textContent = message;
            div.appendChild(p);
            
            messageElement.appendChild(avatar);
            messageElement.appendChild(div);
        } else {
            messageElement.className = "curio-message curio-message--user";
            
            if (imageUrl) {
                const img = document.createElement("img");
                img.src = imageUrl;
                img.alt = "Uploaded image";
                messageElement.appendChild(img);
            }
            
            const p = document.createElement("p");
            p.textContent = message;
            messageElement.appendChild(p);
        }

        imageConversation.appendChild(messageElement);
        imageConversation.scrollTop = imageConversation.scrollHeight;
    }

    async function prepareImageMessage(message) {
        if (!selectedImageFile) return;

        if (imageStatus) imageStatus.textContent = "Analyzing image...";
        if (imageSendButton) imageSendButton.disabled = true;

        const thinkingId = "curio-thinking-" + Date.now();
        const thinkingHtml = `
            <span class="curio-message-avatar" aria-hidden="true">C</span>
            <div>
                <div class="curio-thinking"><i></i><i></i><i></i></div>
            </div>
        `;
        const thinkingElement = document.createElement("article");
        thinkingElement.className = "curio-message curio-message--assistant";
        thinkingElement.id = thinkingId;
        thinkingElement.innerHTML = thinkingHtml;
        
        if (imageConversation) {
            imageConversation.appendChild(thinkingElement);
            imageConversation.scrollTop = imageConversation.scrollHeight;
        }

        try {
            const formData = new FormData();
            formData.append("image", selectedImageFile);
            formData.append("message", message);

            const response = await fetch("/curio/analyze", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                let detail = "Curio could not analyze the image.";
                try {
                    const errorData = await response.json();
                    if (errorData.detail) detail = errorData.detail;
                } catch (_) {}
                throw new Error(detail);
            }

            const data = await response.json();
            
            const thinkingBubble = document.getElementById(thinkingId);
            if (thinkingBubble) thinkingBubble.remove();
            
            // Assume the API might return the answer in `answer` or similar
            const answerText = data.answer || data.result || "Analysis complete.";
            addConversationMessage("curio", answerText);

            if (imageStatus) imageStatus.textContent = "Curio is ready";
        } catch (error) {
            const thinkingBubble = document.getElementById(thinkingId);
            if (thinkingBubble) thinkingBubble.remove();
            
            console.error("Curio image analysis failed:", error);
            if (imageStatus) imageStatus.textContent = "Analysis failed";
            addConversationMessage("curio", `I couldn't process that image. ${error.message}`);
        } finally {
            if (imageSendButton) imageSendButton.disabled = false;
        }
    }

    if (imageMessageForm) {
        imageMessageForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            if (!selectedImageFile || !imageMessageInput) return;

            const message = imageMessageInput.value.trim();
            if (!message) return;

            addConversationMessage("user", message, selectedImageObjectUrl);
            
            if (imageContainer) {
                imageContainer.classList.add('is-hidden');
                setTimeout(() => {
                    imageContainer.hidden = true;
                }, 400);
            }

            imageMessageInput.value = "";
            imageMessageInput.style.height = "auto";

            await prepareImageMessage(message);
        });
    }

    if (imageMessageInput) {
        imageMessageInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                if (imageSendButton && !imageSendButton.disabled) {
                    imageMessageForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                }
            }
        });

        imageMessageInput.addEventListener("input", () => {
            imageMessageInput.style.height = "auto";
            imageMessageInput.style.height = `${Math.min(imageMessageInput.scrollHeight, 140)}px`;
        });
    }

    /*
    ========================================================
    IMAGE VOICE INPUT
    ========================================================
    */
    function setVoiceActiveUI() {
        voiceInputActive = true;
        if (imageMessageInput) speechBaseText = imageMessageInput.value.trim();

        if (imageVoiceButton) {
            imageVoiceButton.classList.add("is-listening");
            imageVoiceButton.setAttribute("aria-pressed", "true");
            imageVoiceButton.setAttribute("aria-label", "Stop voice input");
        }

        if (imageMessageInput) imageMessageInput.placeholder = "Listening…";
        if (imageStatus) imageStatus.textContent = "Curio is listening.";
    }

    function setVoiceInactiveUI(status = "Voice input off") {
        voiceInputActive = false;
        speechBaseText = "";

        if (imageVoiceButton) {
            imageVoiceButton.classList.remove("is-listening");
            imageVoiceButton.setAttribute("aria-pressed", "false");
            imageVoiceButton.setAttribute("aria-label", "Start voice input");
        }

        if (imageMessageInput) imageMessageInput.placeholder = "Ask Curio about this image...";
        if (imageStatus) imageStatus.textContent = "Curio is ready"; // Reset to default
    }

    function startImageVoiceInput() {
        if (!voiceInputSupported) return;
        if (voiceInputActive) {
            stopImageVoiceInput();
            return;
        }
        if (!selectedImageFile) return;

        try {
            if (imageMessageInput) speechBaseText = imageMessageInput.value.trim();
            speechRecognition.start();
        } catch (error) {
            console.warn("Curiora voice input could not start:", error);
        }
    }

    function stopImageVoiceInput() {
        if (!speechRecognition || !voiceInputActive) {
            setVoiceInactiveUI();
            return;
        }

        try {
            speechRecognition.stop();
        } catch (error) {
            console.warn("Curiora voice input could not stop:", error);
            setVoiceInactiveUI();
        }
    }

    if (speechRecognition) {
        speechRecognition.onstart = () => {
            setVoiceActiveUI();
        };

        speechRecognition.onresult = event => {
            let finalTranscript = "";
            let interimTranscript = "";

            for (let index = event.resultIndex; index < event.results.length; index += 1) {
                const result = event.results[index];
                if (result.isFinal) {
                    finalTranscript += result[0].transcript;
                } else {
                    interimTranscript += result[0].transcript;
                }
            }

            const transcript = [speechBaseText, finalTranscript].filter(Boolean).join(" ");
            
            if (imageMessageInput) {
                imageMessageInput.value = [transcript, interimTranscript].filter(Boolean).join(" ");
                imageMessageInput.style.height = "auto";
                imageMessageInput.style.height = `${Math.min(imageMessageInput.scrollHeight, 140)}px`;
            }
        };

        speechRecognition.onerror = event => {
            console.warn("Curiora voice input error:", event.error);
            if (imageStatus) {
                imageStatus.textContent = "Voice input failed or isn't supported.";
                imageStatus.classList.add("is-error");
            }
            setVoiceInactiveUI();
        };

        speechRecognition.onend = () => {
            if (voiceInputActive) {
                setVoiceInactiveUI();
            }
        };
    }

    if (imageVoiceButton) {
        imageVoiceButton.addEventListener("click", startImageVoiceInput);
    }

    /*
    ========================================================
    CAMERA
    ========================================================
    */
    async function startCamera() {
        if (cameraActive) return;

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            if (cameraStatus) cameraStatus.textContent = "Camera access is unavailable.";
            return;
        }

        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: { ideal: "user" } },
                audio: true
            });

            if (cameraPreview) cameraPreview.srcObject = cameraStream;

            cameraActive = true;
            videoPaused = false;
            microphonePaused = false;

            setCameraState();
        } catch (error) {
            console.error("Curiora camera access failed:", error);
            if (cameraStatus) cameraStatus.textContent = "Camera access denied or unavailable.";
        }
    }

    function cancelCamera() {
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
        }
        cameraStream = null;
        if (cameraPreview) cameraPreview.srcObject = null;
        setIdleState();
    }

    if (cameraButton) cameraButton.addEventListener("click", startCamera);
    if (cancelCameraButtons) {
        cancelCameraButtons.forEach(btn => btn.addEventListener("click", cancelCamera));
    }

    if (videoPauseButton) {
        videoPauseButton.addEventListener("click", () => {
            if (!cameraStream) return;
            videoPaused = !videoPaused;
            cameraStream.getVideoTracks().forEach(track => track.enabled = !videoPaused);
            videoPauseButton.textContent = videoPaused ? "Resume video" : "Pause video";
        });
    }

    if (microphonePauseButton) {
        microphonePauseButton.addEventListener("click", () => {
            if (!cameraStream) return;
            microphonePaused = !microphonePaused;
            cameraStream.getAudioTracks().forEach(track => track.enabled = !microphonePaused);
            microphonePauseButton.textContent = microphonePaused ? "Unmute audio" : "Mute audio";
        });
    }

    /*
    ========================================================
    TYPING PLACEHOLDER
    ========================================================
    */
    const placeholders = [
        "Ask anything about an image...",
        "What is in this photo?",
        "Can you describe this scene?",
        "Read the text in this image...",
        "What is happening here?",
    ];
    let placeholderIdx = 0;
    let charIdx = 0;
    let isDeleting = false;
    let typingTimer = null;

    function typePlaceholder() {
        if (!imageMessageInput) return;
        
        if (document.activeElement === imageMessageInput || imageMessageInput.value || voiceInputActive) {
            clearTimeout(typingTimer);
            imageMessageInput.placeholder = "Ask Curio about this image...";
            return;
        }

        const currentText = placeholders[placeholderIdx];
        
        if (isDeleting) {
            imageMessageInput.placeholder = currentText.substring(0, charIdx - 1) + "|";
            charIdx--;
        } else {
            imageMessageInput.placeholder = currentText.substring(0, charIdx + 1) + "|";
            charIdx++;
        }

        let typeSpeed = isDeleting ? 30 : 80;

        if (!isDeleting && charIdx === currentText.length) {
            imageMessageInput.placeholder = currentText; // remove cursor
            typeSpeed = 2500; // Pause at end
            isDeleting = true;
        } else if (isDeleting && charIdx === 0) {
            isDeleting = false;
            placeholderIdx = (placeholderIdx + 1) % placeholders.length;
            typeSpeed = 500; // Pause before new word
        }

        typingTimer = setTimeout(typePlaceholder, typeSpeed);
    }
    
    if (imageMessageInput) {
        imageMessageInput.addEventListener('focus', () => {
            clearTimeout(typingTimer);
            imageMessageInput.placeholder = "Ask Curio about this image...";
        });
        imageMessageInput.addEventListener('blur', () => {
            if (!imageMessageInput.value && !voiceInputActive) {
                typePlaceholder();
            }
        });
        typePlaceholder();
    }

    /*
    ========================================================
    INITIAL STATE
    ========================================================
    */
    setIdleState();
});
