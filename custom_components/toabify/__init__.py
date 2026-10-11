from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import websocket_api
import voluptuous as vol

# On autorise n'importe quel utilisateur connecté à s'abonner
@websocket_api.websocket_command({
    vol.Required("type"): "toastify/subscribe",
})
@callback
def websocket_subscribe_toast(hass, connection, msg):
    @callback
    def forward_toast(event):
        # On transfère l'évènement du bus vers le tunnel WebSocket spécifique
        connection.send_message(websocket_api.event_message(msg["id"], event.data))

    # On écoute le bus interne et on associe l'abonnement à la session en cours
    connection.subscriptions[msg["id"]] = hass.bus.async_listen(
        "toastify_event", forward_toast
    )
    connection.send_result(msg["id"])

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    # Définition du chemin statique
    toast_path_config = StaticPathConfig(
        url_path="/toastify_lib",
        path=hass.config.path("custom_components/toastify/dist"),
        cache_headers=False
    )
    await hass.http.async_register_static_paths([toast_path_config])
    
    # Enregistrement de la commande WebSocket
    websocket_api.async_register_command(hass, websocket_subscribe_toast)

    # Injection JS
    from homeassistant.components.frontend import add_extra_js_url
    add_extra_js_url(hass, "/toastify_lib/toast_engine.js")

    return True
