(function() {
    // Chargement CSS
    if (!document.getElementById('toastify-css')) {
        const link = document.createElement('link');
        link.id = 'toastify-css';
        link.rel = 'stylesheet';
        link.href = '/toastify_lib/toastify.css';
        document.head.appendChild(link);

        const style = document.createElement('style');
        style.innerHTML = `
            @keyframes toast-label-pulse {
                0% { opacity: 1; }
                50% { opacity: 0.2; }
                100% { opacity: 1; }
            }
            /* L'animation s'applique uniquement à l'enfant (le label) */
            .toast-btn-loading .btn-label-text {
                animation: toast-label-pulse 0.8s infinite ease-in-out !important;
            }
            .toast-btn-loading {
                pointer-events: none !important;
                cursor: default;
            }
        `;
        document.head.appendChild(style);
    }

    // Chargement JS
    if (typeof Toastify === "undefined") {
        const script = document.createElement("script");
        script.src = "/toastify_lib/toastify.js";
        script.onload = () => {
            // Hello console
            console.log(
                "%c🍞 TOASTIFY%c Le moteur a été chargé avec succès !", 
                "background-color: #ff9800; color: white; font-weight: bold; border-radius: 4px; padding: 2px 5px;", 
                "color: #ff9800; font-weight: bold;"
            );
            initToastify();
        };
        document.head.appendChild(script);
    } else {
        initToastify();
    }

    // Vérification de la disponibilité de l'objet hass
    function initToastify() {
        const checkHass = setInterval(() => {
            const main = document.querySelector("home-assistant");
            if (main && main.hass) {
                setupListener(main.hass);
                clearInterval(checkHass);
            }
        }, 1000);
    }

    // Thèmes de notifications prédéfinies
    const TOAST_THEMES = {
        "success": "#00b09b",
        "info": "#03a9f4",
        "warning": "#ff9800",
        "error": "#f44336",
        "alert": "#e91e63",
        "default": "rgba(50, 50, 50, 0.9)"
    };

    // Fonction pour déterminer si le message doit être écrit en noir ou en blanc
    // en fonction du thème du toast
    function getContrastColor(hexColor) {
        if (!hexColor || hexColor.includes("gradient")) return "#ffffff";
        
        // Si thème RGBA ou RGB
        if (hexColor.startsWith("rgba") || hexColor.startsWith("rgb")) {
            return "#ffffff";
        }

        // Conversion Hex en RGB
        const hex = hexColor.replace("#", "");
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        
        // Calcul de la luminosité (formule standard YIQ)
        const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
        return (yiq >= 128) ? "#000000" : "#ffffff";
    }

    // Gestionnaire d'actions (URL ou Service HA)
    async function executeAction(actionObj) {
        if (!actionObj) return false;

        // On gère si c'est une simple string (compatibilité) ou un objet
        const action = (typeof actionObj === 'string') ? actionObj.trim() : actionObj.action?.trim();
        const serviceData = actionObj.action_data || {};

        if (!action) return false;

        // URL
        if (action.startsWith("http") || action.startsWith("/")) {
            window.open(action, "_blank");
            return true;
        } 
        // Appel de service Home Assistant
        else if (action.includes(".")) {
            const [domain, service] = action.split(".");
            const hass = document.querySelector("home-assistant")?.hass;
            if (hass) {
                try {
                    await hass.callService(domain, service, serviceData);
                    return true;
                } catch (e) {
                    console.error("[Toastify] Erreur service:", e);
                    return false;
                }
            }
        }
        return false;
    }

    function createToast(data) {
        const d = data;

        if (!d.message) return;

        const visibility = d.visibility || "dashboard";
        const p = window.location.pathname;
        const isDashboard = p.includes("lovelace") || p.includes("dashboard");
        const shouldShow = (visibility === "all" || (visibility === "dashboard" && isDashboard));

        if (shouldShow) {
            const colorInput = d.color ? d.color.toLowerCase() : "default";
            const finalColor = TOAST_THEMES[colorInput] || d.color || TOAST_THEMES["default"];
            const textColor = getContrastColor(finalColor);

            // Container du toast
            const container = document.createElement("div");
            container.style.display = "flex";
            container.style.flexDirection = "row";
            container.style.alignItems = "center";
            container.style.flexGrow = "1";
            container.style.position = "relative";

            // Avatar
            if (d.icon && d.icon.trim() !== "") {
                let iconElement;
                if (d.icon.startsWith("mdi:")) {
                    iconElement = document.createElement("ha-icon");
                    iconElement.setAttribute("icon", d.icon);
                    iconElement.style.setProperty('--mdc-icon-size', '40px');
                    iconElement.style.width = "40px";
                    iconElement.style.height = "40px";
                    iconElement.style.color = textColor;
                } else {
                    iconElement = document.createElement("img");
                    iconElement.src = d.icon;
                    iconElement.style.width = "48px";
                    iconElement.style.height = "48px";
                    iconElement.style.borderRadius = "10px";
                    iconElement.style.objectFit = "cover";
                    iconElement.style.boxShadow = "0 2px 5px rgba(0,0,0,0.15)";
                }
                iconElement.style.marginRight = "14px";
                iconElement.style.flexShrink = "0";
                container.appendChild(iconElement);
            }

            // Container pour le Texte et le Bouton
            const textContainer = document.createElement("div");
            textContainer.style.display = "flex";
            textContainer.style.flexDirection = "column";
            textContainer.style.justifyContent = "center";
            textContainer.style.alignItems = "center";
            textContainer.style.flexGrow = "1"; 
            textContainer.style.paddingRight = "25px";
            
            const textSpan = document.createElement("span");
            textSpan.innerText = d.message;
            textSpan.style.fontSize = "1em";
            textSpan.style.lineHeight = "1.2";
            textSpan.style.fontWeight = "600";
            textSpan.style.color = textColor;
            textContainer.appendChild(textSpan);

            // Toast
            const toastInstance = Toastify({
                node: container,
                duration: d.duration || 5000,
                selector: document.body,
                close: d.close === true || d.close === "true",
                gravity: d.gravity || "top",
                position: d.position || "right",
                // avatar: d.icon || "", // Ajouté au node
                stopOnFocus: true,
                oldestFirst: d.oldestFirst === true || d.oldestFirst === "true",
                style: { 
                    background: finalColor,
                    color: textColor,
                    borderRadius: "10px",
                    boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
                    zIndex: 9999999,
                    position: "fixed",
                    cursor: "default",
                    display: "flex",
                    padding: "8px"
                },
                onClick: function() {
                    toastInstance.hideToast();
                },
                callback: function() {
                    if (d.callback) executeAction(d.callback);
                },
            });

            // Bouton
            if (d.onClick) {
                const btn = document.createElement("button");
                const btnBorder = textColor === "#000000" ? "rgba(0,0,0,0.1)" : "rgba(255,255,255,0.25)";
                btn.innerHTML = `<span class="btn-label-text">${d.onClick.label || "VOIR"}</span>`;
                btn.style.fontSize = "0.75em";
                btn.style.fontWeight = "bold";
                btn.style.letterSpacing = "0.5px";
                btn.style.marginTop = "8px";
                btn.style.padding = "4px 12px";
                btn.style.background = "rgba(0, 0, 0, 0.2)";
                btn.style.border = `1px solid ${btnBorder}`;
                btn.style.color = textColor;
                btn.style.borderRadius = "6px";
                btn.style.fontSize = "0.8em";
                btn.style.cursor = "pointer";
                btn.style.transition = "all 0.3s ease";

                btn.onmouseenter = () => btn.style.background = "rgba(0, 0, 0, 0.4)";
                btn.onmouseleave = () => btn.style.background = "rgba(0, 0, 0, 0.2)";

                btn.onclick = async (e) => {
                    e.stopPropagation();
                    const labelSpan = btn.querySelector('.btn-label-text');
                    const hasFeedback = d.onClick.feedback === true || d.onClick.feedback === "true";

                    if (hasFeedback) {
                        btn.disabled = true;
                        btn.classList.add("toast-btn-loading");
                    }

                    const success = await executeAction(d.onClick);

                    if (hasFeedback) {
                        // On laisse la pulsation au moins 500ms pour que ce soit visible
                        setTimeout(() => {
                            btn.classList.remove("toast-btn-loading");
                            labelSpan.style.transition = "opacity 0.2s ease";
                            labelSpan.style.opacity = "0";
                            
                            setTimeout(() => {
                                if (success) {
                                    btn.innerHTML = `<span class="btn-label-text"><ha-icon icon="mdi:check" style="--mdc-icon-size: 16px; margin-right: 5px;"></ha-icon> EFFECTUÉ</span>`;
                                } else {
                                    btn.innerHTML = `<span class="btn-label-text"><ha-icon icon="mdi:alert-circle" style="--mdc-icon-size: 16px; margin-right: 5px;"></ha-icon> ERREUR</span>`;
                                    btn.style.background = "rgba(255, 0, 0, 0.3)";
                                }

                                const newLabel = btn.querySelector('.btn-label-text');
                                newLabel.style.opacity = "0";

                                setTimeout(() => newLabel.style.opacity = "1", 300);
                                setTimeout(() => toastInstance.hideToast(), 1800);
                            }, 300);
                        }, 1500);
                    } else {
                        setTimeout(() => toastInstance.hideToast(), 500);
                    }
                };
                textContainer.appendChild(btn);
            }

            container.appendChild(textContainer);
            toastInstance.showToast();

            const closeBtn = container.parentElement.querySelector(".toast-close");
            if (closeBtn) {
                closeBtn.style.position = "absolute";
                closeBtn.style.top = "8px";
                closeBtn.style.right = "8px";
                closeBtn.style.opacity = "0.7";
                closeBtn.style.padding = "0";
                closeBtn.style.lineHeight = "1";
            }
        }
    }


    // Abonnement via la commande WebSocket personnalisée
    function setupListener(hass) {
        hass.connection.subscribeMessage(
            (message) => { createToast(message); },
            { type: "toastify/subscribe" }
        ).then(
            null, // Silencieux si tout va bien
            (err) => console.error("[Toastify] Le tunnel a été refusé par le serveur", err)
        );
    }
})();
