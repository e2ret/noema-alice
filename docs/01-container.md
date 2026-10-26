# 1. Контейнер на Proxmox

Один контейнер Ubuntu 24.04 служит сначала стендом для получения root, затем постоянным мостом к HA. Ему нужны свободные порты 53, 80 и 443.

## Шаги

1. Создайте LXC на Ubuntu 24.04. Пример: ID 108, hostname `Alice`, 4 ядра, 8 ГБ RAM, диск 8 ГБ, сеть на `vmbr0`. Закрепите его IP в DHCP роутера (здесь 192.168.1.49).
2. В **Options → Start at boot** включите автозапуск. Без контейнера колонка «глохнет».
3. Освободите порт 53 от systemd-resolved и проверьте интернет:

```bash
systemctl disable --now systemd-resolved
rm /etc/resolv.conf && echo "nameserver 192.168.1.1" > /etc/resolv.conf
touch /etc/.pve-ignore.resolv.conf   # чтобы Proxmox не перезаписал resolv.conf
ping -c 2 github.com
```

4. Поставьте пакеты и стенд lite-kit:

```bash
apt update && apt install -y dnsmasq python3 openssl dnsutils adb git curl ffmpeg
systemctl disable --now dnsmasq       # стенд запускает свой dnsmasq
git clone https://github.com/krevetkqqq/lite-kit ~/lite-kit
ss -tulpn | grep -E ':(53|80|443)\b'  # должно быть пусто
```

## Проверка

`ss` ничего не выводит, `ping github.com` проходит.

Дальше: [2. Root на колонке](02-root.md).
