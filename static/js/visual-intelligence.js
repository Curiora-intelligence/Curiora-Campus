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
    const videoPauseButton = app.querySelector('[data-curio-video-pause]'); // Assume it exists or is added
    const microphonePauseButton = app.querySelector('[data-curio-mic-pause]'); // Assume it exists or is added
    const cancelCameraButton = app.querySelector('[data-curio-close-camera]');
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

        if (cameraContainer) cameraContainer.hidden = true;
        if (imageContainer) imageContainer.hidden = true;
        if (imageConversation) imageConversation.hidden = true;
        if (imageStatus) imageStatus.textContent = "Curio is ready";
        
        if (videoPauseButton) videoPauseButton.textContent = "Video pause";
        if (microphonePauseButton) microphonePauseButton.textContent = "Microphone pause";

        if (imageVoiceButton) {
            imageVoiceButton.classList.remove("is-listening");
            imageVoiceButton.setAttribute("aria-pressed", "false");
        }
        
        app.classList.remove("camera-active", "camera-paused");
    }

    function setCameraState() {
        if (cameraContainer) cameraContainer.hidden = false;
        if (imageContainer) imageContainer.hidden = true;
        if (imageConversation) imageConversation.hidden = true;

        if (cameraStatus) cameraStatus.textContent = "Curio is observing";
        
        app.classList.add("camera-active");
    }

    function setImageState() {
        if (cameraContainer) cameraContainer.hidden = true;
        if (imageContainer) imageContainer.hidden = false;
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
    function addConversationMessage(role, message) {
        if (!imageConversation) return;

        const messageElement = document.createElement("div");
        messageElement.className = `image-message ${role}`;
        messageElement.textContent = message;

        imageConversation.appendChild(messageElement);
        imageConversation.scrollTop = imageConversation.scrollHeight;
    }

    async function prepareImageMessage(message) {
        if (!selectedImageFile) return;

        if (imageStatus) imageStatus.textContent = "Analyzing image...";
        if (imageSendButton) imageSendButton.disabled = true;

        try {
            const formData = new FormData();
            formData.append("image", selectedImageFile);
            formData.append("message", message);

            const response = await fetch("/api/visual-intelligence/analyze", {
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
            
            // Assume the API might return the answer in `answer` or similar
            const answerText = data.answer || data.result || "Analysis complete.";
            addConversationMessage("curio", answerText);

            if (imageStatus) imageStatus.textContent = "Curio is ready";
        } catch (error) {
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

            addConversationMessage("user", message);

            imageMessageInput.value = "";
            imageMessageInput.style.height = "auto";

            await prepareImageMessage(message);
        });
    }

    if (imageMessageInput) {
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
    if (cancelCameraButton) cancelCameraButton.addEventListener("click", cancelCamera);

    /*
    ========================================================
    INITIAL STATE
    ========================================================
    */
    setIdleState();
});
