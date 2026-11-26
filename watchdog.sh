#!/data/data/com.termux/files/usr/bin/bash
cd ~/amora_yangi
while true; do
    if ! pgrep -f "python -u main.py" > /dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M')] Bot o'chgan — qayta ishga tushirilmoqda..." >> watchdog.log
        nohup python -u main.py >> bot.log 2>&1 &
    fi
    sleep 60
done
