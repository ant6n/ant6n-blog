for file; do
  base=$(basename $file)
  dir=$(dirname $file)
  convert $file -level 24%,92%,1.5 $dir/adjusted-$base
done

