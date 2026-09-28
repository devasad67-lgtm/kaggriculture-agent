cd /d/kaggle
for dn in l48mc l8omc; do
  cat ladder/$dn/ids.txt | xargs -P 6 -I{} sh -c "[ -f ladder/$dn/episode-{}-replay.json ] || kaggle competitions replay {} -p ladder/$dn >/dev/null 2>&1"
done
ls ladder/l48mc ladder/l8omc | wc -l
