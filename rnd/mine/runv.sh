cd /d/kaggle
for n in vA vB vC; do rm -f rnd/rt/$n.jsonl; .venv/Scripts/python.exe rnd/rtbatch.py bots/L48_$n/main.py rnd/rt/$n.jsonl $(cat rnd/mine/close2.txt) > /dev/null 2>&1; done
echo done
