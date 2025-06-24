# YouTubeDownloader

## The setup is done for the machine

- OS: Ubuntu 24.04.2 LTS
- Platform: x86_64
- Processor: Intel(R) Core(TM) i5-6500 CPU @ 3.20GHz (4 cores)
- RAM: 32GB DDR4 2133 MHz
- Storage: SSD 120GB

## Ports used (server):
- 22 - SSH - управление сервером. Вход только по ключу
- 2468 - YouTubeDownloader (web)

## Ports used (balancer):
- 22 - SSH - управление сервером. Вход только по ключу
- 80 - HHTP - веб-интерфейс (витрина). Возвращает постоянное перенаправление на HTTPs
- 443 - HTTPs - веб-интерфейс (витрина).

## Добавим нового пользователя
Работаем от root

Пользователь name:password

```
adduser name
usermod -aG sudo name
su - name
sudo ls -la /root
sudo reboot
```

## Создадим ключи для SSH
Работаем от root

```
ssh-keygen
cd .ssh
ls -l
nano id_rsa
mv id_rsa.pub authorized_keys
chmod 644 authorized_keys
```
Скопируем содержимое закрытого ключа из консоли и сохраним его в пустом формате на ПК с помощью текстового редактора

Имя файла не критично. Важно: приватный ключ должен содержать:
-----НАЧНИТЕ ОТКРЫВАТЬ ЗАКРЫТЫЙ КЛЮЧ OPENSSH----- ... -----END OPENSSH ПРИВАТНЫЙ КЛЮЧ-----

Публичный ключ скопируем всем пользователям в папку .ssh

Права 644 нужно сделать у всех пользователей

В Windows загрузим PuTTYgen. В меню: нажмите Conversions->Import key и найдем сохраненный файл закрытого ключа
Он загрузится в программу. Нажмем «Сохранить закрытый ключ» в формате PuTTY .ppk в D:\Program Files\PuTTY\KEYs
Загрузим файл .ppk в свой профиль SSH уже в программе PuTTY: Connection->SSH->Auth->Credentials
Connection - keepAlive 15 sec
Сохраним свой профиль в PuTTY

## Запретим на вход по паролю
Работаем от root

nano /etc/ssh/sshd_config:
```
PubkeyAuthentication yes
PasswordAuthentication no
```
service ssh restart

## Обновим систему
Работаем от name
```
sudo apt update
sudo apt upgrade
sudo reboot
sudo apt-get install python3-pip
sudo apt install python3.12-venv
sudo apt-get install ffmpeg
```

## Копируем исходные файлы
Работаем от name

Создаем папку ogg2mpeg. Копируем в неё исходные файлы

Даем права на исполнение (!!! Дать папке /home/name права на R+X other, командой chmod o+rX /home/name):
```
find ogg2mpeg/ -type f -exec chmod 755 {} \;
```

## Создаем виртуальное окружение
Работаем от name

Версии добавленных пакетов:
```
annotated-types   0.7.0
anyio             4.8.0
click             8.1.8
fastapi           0.115.7
h11               0.14.0
idna              3.10
pip               24.0
pydantic          2.10.6
pydantic_core     2.27.2
pydub             0.25.1
python-multipart  0.0.20
sniffio           1.3.1
starlette         0.45.3
typing_extensions 4.12.2
uvicorn           0.34.0
```

```
cd /home/pi/ogg2mpeg
python3 -m venv myenv
source myenv/bin/activate
pip install fastapi uvicorn pydub python-multipart
pip list
python main.py -- Эту команду не запускать! Это только для ручного тестирования
```

## Добавляем сервисы в systemD
Работаем от name

Для простого испытания достаточно - python3 main.py

sudo nano /etc/systemd/system/ogg2mpeg.service (python3.12?):
```
[Unit]
Description=ogg2mpeg
After=network-online.target nss-user-lookup.target

[Service]
User=name
Group=name
WorkingDirectory=/home/pi/ogg2mpeg
Environment="PYTHONPATH=/home/pi/ogg2mpeg/myenv/lib/python3.12/site-packages"
ExecStartPre=/usr/bin/sleep 10
ExecStart=/home/pi/ogg2mpeg/myenv/bin/python3.12 /home/pi/ogg2mpeg/main.py

RestartSec=10
Restart=always
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Настраивам systemD:
```
sudo systemctl daemon-reload
sudo systemctl enable --now ogg2mpeg.service
systemctl status ogg2mpeg.service
```

