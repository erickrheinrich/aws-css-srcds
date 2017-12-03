#!/bin/bash

dpkg --add-architecture i386
apt-get update
apt-get -y upgrade
apt-get -y install wget lib32gcc1 lib32tinfo5 libc6:i386 libexpat1:i386 libgcc1:i386 libstdc++6:i386 unzip
useradd -ms /bin/bash steam
chown -R steam:steam /tmp/mods /tmp/cfg
su - steam -c '/tmp/css-install-script.sh'
cat > /lib/systemd/system/css-server.service <<css-server-EOF
[Unit]
Description=Counter-Strike Source Dedicated Server
After=network.target

[Service]
WorkingDirectory=/home/steam/css
Environment="LD_LIBRARY_PATH=/home/steam/css/:/home/steam/css/bin"
User=steam

ExecStartPre=/home/steam/css/steamcmd.sh +login anonymous +force_install_dir ./css +app_update 232330 validate +quit
ExecStart=/home/steam/css/srcds_run -game cstrike +exec server.cfg +rcon_password "$RCON_PASSWORD" +map de_dust2

TimeoutStartSec=0
Restart=always

[Install]
WantedBy=default.target
css-server-EOF