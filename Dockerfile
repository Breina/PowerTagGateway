FROM ghcr.io/home-assistant/home-assistant:latest

# HA
EXPOSE 8123:8123/tcp

# HA Python debugging
EXPOSE 5678:5678/tcp

# HA Python debugging
EXPOSE 3702:3702/udp


COPY staging/.storage /config/.storage

COPY staging/configuration.yaml /config/configuration.yaml

COPY custom_components /config/custom_components
