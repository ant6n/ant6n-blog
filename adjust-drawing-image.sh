# adsjusts the note-8 hand-drawn images
# turns png images into jpg files
for file; do
  base=$(basename $file)
  dir=$(dirname $file)
  ext=${base#*.}
  name=${base%.*}
  if [[ $ext == "jpg" ]]; then
      echo ERROR: $file is already a jpg
      exit 1
  fi
  convert $file -level 24%,92%,1.5 -quality 90  $dir/$name.jpg
done

