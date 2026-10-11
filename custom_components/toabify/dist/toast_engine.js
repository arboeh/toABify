(function() {
    "use strict";

    /**
     * Load a CSS stylesheet or JavaScript file into document head.
     * Skips loading if an element with the given id already exists.
     *
     * @param {string} id - Unique identifier for the resource element
     * @param {"link"|"script"} type - HTML element type to create
     * @param {string} src - URL/path to the resource source
     * @returns {HTMLElement|null} The created element, or null if resource already loaded
     * @private
     */
    const loadResource = (id, type, src) => {
        if (document.getElementById(id)) {
            return null;
        }

        const element = document.createElement(type);
        element.id = id;

        if (type === "link") {
            element.rel = "stylesheet";
            element.href = src;
        } else if (type === "script") {
            element.src = src;
        }

        document.head.appendChild(element);
        return element;
    };

    /**
     * Predefined notification theme colors.
     * @readonly
     * @type {Object.<string, string>}
     */
    const TOAST_THEMES = {
        "success": "#00b09b",
        "info": "#03a9f4",
        "warning": "#ff9800",
        "error": "#f44336",
        "alert": "#e91e63",
        "default": "rgba(50, 50, 50, 0.9)"
    };

    /**
     * CSS keyframe animation for button loading state.
     * Pulses the button label during async action feedback.
     *
     * @type {string}
     */
    const PULSE_STYLE = "\n        @keyframes toast-label-pulse {\n            0% { opacity: 1; }\n            50% { opacity: 0.2; }\n            100% { opacity: 1; }\n        }\n        /* The animation applies only to the child element (the label) */\n        .toast-btn-loading .btn-label-text {\n            animation: toast-label-pulse 0.8s infinite ease-in-out !important;\n        }\n        .toast-btn-loading {\n            pointer-events: none !important;\n            cursor: default;\n        }\n    ";

    /**
     * Calculate text color (black or white) that contrasts with a background color.
     * Uses the YIQ brightness formula to determine optimal readability.
     *
     * @param {string} hexColor - Background color in hex (#RRGGBB), rgb(), or rgba() format
     * @returns {string} "#000000" for dark backgrounds, "#ffffff" for light/undefined
     * @private
     */
    const getContrastColor = (hexColor) => {
        if (!hexColor || hexColor.includes("gradient")) {
            return "#ffffff";
        }

        if (hexColor.startsWith("rgba") || hexColor.startsWith("rgb")) {
            return "#ffffff";
        }

        const hex = hexColor.replace("#", "");
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);

        const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        return brightness >= 128 ? "#000000" : "#ffffff";
    };

    /**
     * Execute a button or callback action.
     * Handles URL opening (http/https/slash-prefixed) and Home Assistant service calls.
     *
     * @async
     * @param {Object|string|null|undefined} actionObj - Action configuration or URL string
     * @param {string} [actionObj.action] - Action string (URL or "domain.service")
     * @param {Object} [actionObj.action_data] - Service call parameters
     * @returns {Promise<boolean>} Resolves to true if action executed successfully
     * @private
     */
    const executeAction = async (actionObj) => {
        if (!actionObj) return false;

        const action = typeof actionObj === "string"
            ? actionObj.trim()
            : actionObj.action?.trim();
        const serviceData = actionObj.action_data ?? {};

        if (!action) return false;

        if (action.startsWith("http") || action.startsWith("/")) {
            window.open(action, "_blank");
            return true;
        }

        if (action.includes(".")) {
            const [domain, service] = action.split(".");
            const hass = document.querySelector("home-assistant")?.hass;

            if (!hass) {
                return false;
            }

            try {
                if (!hass.callService) {
                    return false;
                }
                await hass.callService(domain, service, serviceData);
                return true;
            } catch (error) {
                console.error("[Toastify] Service error:", error);
                return false;
            }
        }

        return false;
    };

    /**
     * Create a toast notification with message, styling, icon, and optional action button.
     * Respects visibility policy - "dashboard" toasts only show on dashboard pages.
     *
     * @param {Object} data - Toast configuration object
     * @param {string} data.message - Toast message content (required)
     * @param {string} [data.color='default'] - Color theme (success, info, warning, error, etc.) or hex value
     * @param {number} [data.duration=5000] - Auto-dismiss duration in milliseconds
     * @param {string} [data.icon] - MDI icon name ("mdi:bell") or image URL
     * @param {string} [data.visibility='dashboard'] - 'all' or 'dashboard'
     * @param {string} [data.position='right'] - Horizontal position (left, center, right)
     * @param {string} [data.gravity='top'] - Vertical position (top, bottom)
     * @param {boolean|string} [data.close=false] - Whether to show close button
     * @param {boolean|string} [data.oldestFirst=false] - Toast stack ordering
     * @param {Object} [data.onClick] - Button configuration
     * @param {string} [data.onClick.action] - Button action URL or service
     * @param {string} [data.onClick.label='CLOSE'] - Button label text
     * @param {boolean|string} [data.onClick.feedback] - Show success/error feedback
     * @param {*} [data.callback] - Server-side callback action
     * @returns {void}
     * @private
     */
    const createToast = (data) => {
        const d = data;

        if (!d.message) return;

        const visibility = d.visibility || "dashboard";
        const p = window.location.pathname;
        const isDashboard = p.includes("lovelace") || p.includes("dashboard");
        const shouldShow = (visibility === "all" || (visibility === "dashboard" && isDashboard));

        if (!shouldShow) {
            return;
        }

        const colorInput = d.color ? d.color.toLowerCase() : "default";
        const finalColor = TOAST_THEMES[colorInput] || d.color || TOAST_THEMES["default"];
        const textColor = getContrastColor(finalColor);

        // Toast container
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
                iconElement.style.setProperty("--mdc-icon-size", "40px");
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

        // Container for text and button
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

        // Toast instance
        const toastInstance = Toastify({
            node: container,
            duration: d.duration || 5000,
            selector: document.body,
            close: d.close === true || d.close === "true",
            gravity: d.gravity || "top",
            position: d.position || "right",
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

        // Button
        if (d.onClick) {
            const btn = document.createElement("button");
            const btnBorder = textColor === "#000000" ? "rgba(0,0,0,0.1)" : "rgba(255,255,255,0.25)";
            btn.innerHTML = '<span class="btn-label-text">' + (d.onClick.label || "CLOSE") + '</span>';
            btn.style.fontSize = "0.8em";
            btn.style.fontWeight = "bold";
            btn.style.letterSpacing = "0.5px";
            btn.style.marginTop = "8px";
            btn.style.padding = "4px 12px";
            btn.style.background = "rgba(0, 0, 0, 0.2)";
            btn.style.border = "1px solid " + btnBorder;
            btn.style.color = textColor;
            btn.style.borderRadius = "6px";
            btn.style.cursor = "pointer";
            btn.style.transition = "all 0.3s ease";

            btn.onmouseenter = () => btn.style.background = "rgba(0, 0, 0, 0.4)";
            btn.onmouseleave = () => btn.style.background = "rgba(0, 0, 0, 0.2)";

            btn.onclick = async (e) => {
                e.stopPropagation();
                const labelSpan = btn.querySelector(".btn-label-text");
                const hasFeedback = d.onClick.feedback === true || d.onClick.feedback === "true";

                 if (hasFeedback) {
                     btn.disabled = true;
                     btn.classList.add("toast-btn-loading");
                 }

                 const success = await executeAction(d.onClick);

                 if (hasFeedback) {
                     // Keep the pulse for at least 500ms so it's visible
                     setTimeout(() => {
                         btn.classList.remove("toast-btn-loading");
                         const labelSpan = btn.querySelector(".btn-label-text");
                         labelSpan.style.transition = "opacity 0.2s ease";
                         labelSpan.style.opacity = "0";

                         setTimeout(() => {
                             if (success) {
                                 btn.innerHTML = '<span class="btn-label-text"><ha-icon icon="mdi:check" style="--mdc-icon-size: 16px; margin-right: 5px;"></ha-icon> DONE</span>';
                             } else {
                                 btn.innerHTML = '<span class="btn-label-text"><ha-icon icon="mdi:alert-circle" style="--mdc-icon-size: 16px; margin-right: 5px;"></ha-icon> ERROR</span>';
                                 btn.style.background = "rgba(255, 0, 0, 0.3)";
                             }

                             const newLabel = btn.querySelector(".btn-label-text");
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

        const closeBtn = container.parentElement?.querySelector(".toast-close");
        if (closeBtn) {
            closeBtn.style.position = "absolute";
            closeBtn.style.top = "8px";
            closeBtn.style.right = "8px";
            closeBtn.style.opacity = "0.7";
            closeBtn.style.padding = "0";
            closeBtn.style.lineHeight = "1";
        }
    };

    /**
     * Subscribe to WebSocket messages for toast notifications.
     *
     * @param {Object} hass - Home Assistant instance with active WebSocket connection
     * @param {Object} hass.connection - WebSocket connection object
     * @param {Function} hass.connection.subscribeMessage - Subscription callback handler
     * @returns {void}
     * @private
     */
    const setupListener = (hass) => {
        hass.connection?.subscribeMessage?.(
            (message) => { createToast(message); },
            { type: "toastify/subscribe" }
        )?.then?.(
            null, // Silent on success
            (err) => console.error("[Toastify] Connection refused by server", err)
        );
    };

    /**
     * Initialize Toastify engine by polling for the Home Assistant instance.
     * Waits until the home-assistant element exposes the hass object,
     * then subscribes to WebSocket toast messages.
     *
     * @returns {void}
     * @private
     */
    const initToastify = () => {
        const checkHass = setInterval(() => {
            const main = document.querySelector("home-assistant");
            if (main?.hass) {
                setupListener(main.hass);
                clearInterval(checkHass);
            }
        }, 1000);
    };

    // Load CSS stylesheet
    loadResource("toastify-css", "link", "/toastify_lib/toastify.css");

    // Inject custom keyframe pulse style for button feedback
    const style = document.createElement("style");
    style.innerHTML = PULSE_STYLE;
    document.head.appendChild(style);

    // Load Toastify JS library
    const script = loadResource("toastify-js", "script", "/toastify_lib/toastify.js");
    if (script) {
        script.onload = () => {
            console.log(
                "%c🍞 TOASTIFY%c Engine loaded successfully!",
                "background-color: #ff9800; color: white; font-weight: bold; border-radius: 4px; padding: 2px 5px;",
                "color: #ff9800; font-weight: bold;"
            );
            initToastify();
        };
        script.onerror = () => {
            console.error("[Toastify] Failed to load library");
            initToastify();
        };
    } else {
        initToastify();
    }
})();
