# YouTubeDownloader

## Setting up for the machine

- OS: Ubuntu 24.04.2 LTS
- Platform: x86_64
- Processor: Intel(R) Core(TM) i5-6500 CPU @ 3.20GHz (4 cores)
- RAM: 32GB DDR4 2133 MHz
- Storage: SSD 120GB

## Ports used (server):
- 22 - SSH - server management. Login only by key
- 2468 - YouTubeDownloader (web)

## Ports used (balancer):
- 22 - SSH - balancer control. Login only by key
- 80 - HHTP - web interface (web). Returns permanent redirect to HTTPs
- 443 - HTTPs - web interface (web).

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

