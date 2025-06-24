# YouTubeDownloader

## Setting up for the server

- Processor / Memory: Intel(R) Core(TM) i5-6500 CPU @ 3.20GHz (4 cores) / 32GB DDR4 2133 MHz
- OS / Platform: Ubuntu 24.04.2 LTS / x86_64
- Storage: SSD 120GB

## Setting up for the balancer

- Processor / Memory - VIA Eden Processor 1000MHz (32bit) / 2GB DDR2
- AlpineLinux version / Linux kernel version - 3.21.3 / 6.12.13-0-lts
- HAProxy version 3.0.9-7f0031e 2025/03/20
- Storage: SSD 4GB

## Ports used (server):
- 22 - SSH - server management. Login only by key
- 2468 - HTTP - YouTubeDownloader

## Ports used (balancer):
- 22 - SSH - balancer control. Login only by key
- 80 - HHTP - web interface. Returns permanent redirect to HTTPs
- 443 - HTTPs - web interface. HaProxy
- 444 - HTTPs - Alpine Configuration Framework
- 8404/stats - HTTP - HaProxy statistics

# Setting up the server (192.168.8.202)

## Add a new user
Working as root

User name:password
```
adduser name
usermod -aG sudo name
su - name
sudo ls -la /root
sudo reboot
```

## Create keys for SSH
Working as root

```
ssh-keygen
cd .ssh
ls -l
nano id_rsa
mv id_rsa.pub authorized_keys
chmod 644 authorized_keys
```
Copy the contents of the private key from the console and save it in an empty format on your PC using a text editor.
The file name is not critical. Important: the private key must contain:
```
-----START OPENSH PRIVATE KEY-----
...
-----END OPENSSH ПРИВАТНЫЙ КЛЮЧ-----
```
Copy the public key to all users in the .ssh folder.
You need to set 644 rights for all users.
In Windows, load PuTTYgen. In the menu: click Conversions->Import key and find the saved private key file.
It will load into the program. Click "Save private key" in PuTTY .ppk format in D:\Program Files\PuTTY\KEYs.
Load the .ppk file into your SSH profile in the PuTTY program: Connection->SSH->Auth->Credentials
Connection - keepAlive 15 sec
Saving your profile in PuTTY

## We prohibit login by password
We work as root

nano /etc/ssh/sshd_config:
```
PubkeyAuthentication yes
PasswordAuthentication no
```
service ssh restart

## We will update the system
We work from name
```
sudo apt update
sudo apt upgrade
sudo reboot
sudo apt-get install python3-pip
sudo apt install python3.12-venv
sudo apt-get install ffmpeg
```

## Copying source files
Working from name

Create a youtubedownloader folder. Copy the source files into it.

Give execution rights (!!! Give the /home/name folder rights to R+X other, with the chmod o+rX /home/name command):
```
find ogg2mpeg/ -type f -exec chmod 755 {} \;
```

## Create a virtual environment
Working from name

Versions of added packages:
```
annotated-types   0.7.0
anyio             4.9.0
click             8.2.1
fastapi           0.115.13
h11               0.16.0
idna              3.10
Jinja2            3.1.6
MarkupSafe        3.0.2
pip               24.0
pydantic          2.11.7
pydantic_core     2.33.2
python-multipart  0.0.20
sniffio           1.3.1
starlette         0.46.2
typing_extensions 4.14.0
typing-inspection 0.4.1
uvicorn           0.34.3
yt-dlp            2025.6.9
```

```
cd /home/name/youtubedownloader
python3 -m venv myenv
source myenv/bin/activate
pip install fastapi uvicorn jinja2 yt-dlp python-multipart
pip list
python app.py -- Do not run this command! This is for manual testing only.
```

## Adding services to systemD
Working from name

For a simple test it is enough - python3 app.py

sudo nano /etc/systemd/system/youtubedownloader.service (python3.12?):
```
[Unit]
Description=youtubedownloader
After=network-online.target nss-user-lookup.target

[Service]
User=name
Group=name
WorkingDirectory=/home/name/youtubedownloader
Environment="PYTHONPATH=/home/name/youtubedownloader/myenv/lib/python3.12/site-packages"
ExecStartPre=/usr/bin/sleep 10
ExecStart=/home/name/youtubedownloader/myenv/bin/python3.12 /home/name/youtubedownloader/app.py
??? ExecStart=/home/name/youtubedownloader/uvicorn app:app --reload --host 0.0.0.0 --port 2468 ???

RestartSec=10
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Configure systemD:
```
sudo systemctl daemon-reload
sudo systemctl enable --now youtubedownloader.service
systemctl status youtubedownloader.service
```

# Setting up a balancer (78.10.22.114 - 192.168.8.201)

The setting is made for the domain:
```
youtubedownloader.by
```

## Added new repositories for updating packages
```
vi /etc/apk/repositories
	I
	http://dl-cdn.alpinelinux.org/alpine/v3.21/main
	http://dl-cdn.alpinelinux.org/alpine/v3.21/community
	Esc
	:wq
 ```

## We will update the system
```
apk update
apk upgrade
```

## Enter an additional folder for commits (this folder is not included in the list for commits by default)
```
lbu include /etc/init.d/
```

## Moving the ACF system service from port 443 to port 444 (to free up port 443 for HaProxy)
```
vi /etc/mini_httpd/mini_httpd.conf
	I
	port=444
	Esc
	:wq
rc-service mini_httpd restart
 ```

## Install HaProxy and add autoload
```
apk add haproxy
haproxy version
rc-update add haproxy default
rc-service haproxy start
rc-service haproxy status
```

## Installing certBot
```
apk add certbot
certbot --version
```

## Configure HaProxy (/etc/haproxy/haproxy.cfg)
```
global
    maxconn 4096
defaults
    log global
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s
frontend http_front
    bind *:80
    acl letsencrypt-acl path_beg /.well-known/acme-challenge/
    redirect scheme https code 301 if !letsencrypt-acl
    use_backend letsencrypt-backend if letsencrypt-acl
frontend https_front
    bind *:443 ssl crt /etc/haproxy/certs/
    acl host_site1 hdr(host) -i youtubedownloader.by
    use_backend youtubedownloader if host_site1
    default_backend backend_default
backend letsencrypt-backend
    server certbot 127.0.0.1:1111
backend youtubedownloader
    server server:2468 192.168.8.201:2468 check
backend backend_default
    errorfile 503 /etc/haproxy/errors/503.http
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats realm HAProxy\ Statistics
    stats auth admin123:pass123
    stats admin if TRUE
    stats refresh 60
```

## Page for statistics Haroxy (admin123:pass123)
```
http://192.168.4.201:8404/stats
```

## Check the configuration file and restart HaProxy
```
haproxy -c -f /etc/haproxy/haproxy.cfg
rc-service haproxy reload
```

## Create a primary certificate for the domain. File youtubedownloader.sh (you need to create a folder for the combined certificate - mkdir /etc/haproxy/certs)
```
#!/bin/sh
cat /etc/letsencrypt/live/youtubedownloader.by/fullchain.pem /etc/letsencrypt/live/youtubedownloader.by/privkey.pem > /etc/haproxy/certs/youtubedownloader.by.pem
rc-service haproxy reload
```

## We create certificates
```
chmod +x /root/youtubedownloader.sh
certbot certonly --standalone --http-01-port 1111 -d youtubedownloader.by --post-hook "/root/youtubedownloader.sh"
```

## Create a script for automatic certificate reissue autoCertBot.sh (and make it executable chmod +x /root/autoCertBot.sh)
```
#!/bin/bash
LOG_FILE="/root/haproxy_cert_update.log"

CERT_DIR="/etc/letsencrypt/live"
HAPROXY_CERT_DIR="/etc/haproxy/certs"
DOMAINS=("youtubedownloader.by")

echo "[$(date)] Starting certificate update..." >> "$LOG_FILE"

for domain in "${DOMAINS[@]}"; do
    if [ -f "$CERT_DIR/$domain/fullchain.pem" ] && [ -f "$CERT_DIR/$domain/privkey.pem" ]; then
        cat "$CERT_DIR/$domain/fullchain.pem" "$CERT_DIR/$domain/privkey.pem" > "$HAPROXY_CERT_DIR/$domain.pem"
        echo "[$(date)] Certificate for $domain updated successfully." >> "$LOG_FILE"
    else
        echo "[$(date)] ERROR: Certificate files for $domain are missing!" >> "$LOG_FILE"
    fi
done

# Проверка конфигурации HAProxy
haproxy -c -f /etc/haproxy/haproxy.cfg >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    rc-service haproxy reload >> "$LOG_FILE" 2>&1
    echo "[$(date)] HAProxy reloaded successfully." >> "$LOG_FILE"
else
    echo "[$(date)] ERROR: Invalid HAProxy configuration." >> "$LOG_FILE"
fi

echo "[$(date)] Certificate update process finished." >> "$LOG_FILE"
```

## We set the crown to check every 12 hours
```
crontab -e
	0 */12 * * * certbot renew --quiet
```

## To save a commit to Alpine's persistent memory, use the command
```
lbu commit
```

## Restart and recheck
```
reboot
```
