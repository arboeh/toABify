from homeassistant.components.notify import BaseNotificationService
from homeassistant.helpers.event import async_call_later
from homeassistant.core import Context, EventOrigin, callback
from homeassistant.util.async_ import run_callback_threadsafe

def get_service(hass, config, discovery_info=None):
    return ToastifyNotificationService(hass)

class ToastifyNotificationService(BaseNotificationService):
    def __init__(self, hass):
        self.hass = hass

    def send_message(self, message="", **kwargs):
        data = kwargs.get("data") or {}
        duration = data.get("duration", 3000)
        callback_data = data.get("callback")
        js_callback = None
        
        if isinstance(callback_data, str):
            if callback_data.startswith("/") or callback_data.startswith("http"):
                js_callback = callback_data

        event_data = {
            "message": message,
            "duration": data.get("duration", 5000),
            "close": data.get("close", False),
            "position": data.get("position", "right"),
            "gravity": data.get("gravity", "top"),
            "icon": data.get("icon", data.get("avatar", "")),
            "color": data.get("color", "info"),
            "visibility": data.get("visibility", "dashboard"),
            "button_label": data.get("button_label", "VOIR"),
            "oldestFirst": data.get("oldestFirst", True),
            "onClick": data.get("onClick"),
            "callback": js_callback,
        }

        # Envoi au Frontend
        @callback
        def fire_event():
            self.hass.bus.async_fire("toastify_event", event_data, origin=EventOrigin.local, context=Context())

        run_callback_threadsafe(self.hass.loop, fire_event)

        # Gestion du Callback côté serveur (Services HA)
        if isinstance(callback_data, dict):
            action = callback_data.get("action", "")
            if "." in action:
                domain, service = action.split(".")
                service_params = callback_data.get("action_data", {})

                async def execute_callback(_):
                    await self.hass.services.async_call(domain, service, service_params)

                if duration > 0:
                    async_call_later(self.hass, duration / 1000, execute_callback)
