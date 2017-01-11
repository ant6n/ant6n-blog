Title: Extracting Location Data from Vector pdf Maps with Inkscape/Svg/Python/Xpath
Slug: 2013-04-13-extract-pdf
Date: 2013-04-13 18:00:00
status: published

*This post was moved from a now defunct blog of mine*

When I published my recent
[visualization of populations near Montreal train stations](http://www.cat-bus.com/2013/04/walksheds-visualizedshowing-populations-near-montreal-rail-stations/),
some people told me that I should consider extending it with data
showing work places as well. This makes sense as a way to gauge
ridership. People go from home to work, so work places are an
indicator of potential ridership just as much as population (if not
more – every work place is being traveled to, but not every home place
is being travelled from).

The problem is that I couldn’t find much useful data for work
places. This may just be my bad googling skills, or maybe census data
should be easier to find. In any case, I found these maps from the
2006 census, showing places of work on maps. The maps come in pdf
format and are vectorized. Dots represent some number of workers, for
the Montreal map every dot represents 500 workers:

<img style="width: 100%; display:block; margin-left:auto; margin-right: auto" src="{filename}/images/extract-pdf/1pdfdots.png">
[//]: ![dots]({filename}/images/extract-pdf/1pdfdots.png)

Now this seems like a bad source to extract data, but not all is
lost. Being in a vectorized format, we can actually extract the
location of the dots. And if we rectify the image using a couple of
geo references, we can transform the location of the dots back to
lat/lng points. The following process is a bit hacky, and not entirely
accurate (the dots’ accuracy should be around 100m), but it provides a
quick(ish) and dirty way to extract the data.

1. Prepare data for extraction
------------------------------

The way vectorized pdfs can be dealt with beautifully is [Inkscape](http://inkscape.org/). It
is basically an open source version of Adobe Illustrator, it is to
Illustrator as Gimp is to Photoshop. The software is really useful for
our purposes because it allows importing vectorized pdf files, it
allows editing them, and it stores imagery data as [svg files](http://en.wikipedia.org/wiki/Scalable_Vector_Graphics). Being an
xml, we can extract our information right out of Inkscape produced
files using python and xml libraries. It really is my go-to solution
for scraping non-text information out of pdfs.

In order to extract the data, we have to first prepare at a bit
though. After importing the svg into Inkscape, we have to make sure
all our data can easily be extracted. For the Montreal Work Place pdf,
I first separated the data into multiple layers. I was interested in
the dots. They were actually grouped together in one group. This is
not good, because locations of objects inside groups are stored
relative to the position of the group. We need the objects as paths
living directly in the layer, so the objects need to be
ungrouped. This gave me 3473 objects of type group (see the image
below). Apparently the dots are all inside groups containing the
single dot. So we need to ungroup again.

<img style="width: 100%; display:block; margin-left:auto; margin-right: auto" src="{filename}/images/extract-pdf/2preparedata.png">

The next problem is that the data is at the center of the dots, but
the dots were represented by paths of four nodes, forming a circle. In
order for the first node in the path to correspond to the data, we
simple resize the dots, individually until they are so small that the
circle becomes invisibly small.

We also need a way to extract the points later in python, so we need a
way to differentiate those path objects from other path objects. The
simple way in this case was to select them based on their color – all
the dots and only the dots have a fill property with value
`#de2d26`. Properties like these can easily be found by using Inkscape’s
builtin xml editor (Edit-›Xml Editor).

So now my data was prepared. I knew that all the data was in the paths
which have a fill property of `#de2d26`, and its location corresponded
to the first node in the path.

2. Find geo-references
----------------------

We can now extract the data, but we will only know the image
coordinates of the data. In order to get the world coordinates of the
data (i.e. lat/lng values), we need to find the projection that the
image uses. This could be done with geo-referencing tools that come
with software like QuantumGIS. But since our map covers a small
geographical area, an affine Transformation between the pdf map and
the

<img style="width: 100%; display:block; margin-left:auto; margin-right: auto" src="{filename}/images/extract-pdf/3makerefs.png">

I created 12 such reference points, so that the errors I make in
creating them will (hopefully) cancel out.

3. The extraction script
------------------------

In the final step I used the below script to extract the data. It’s
written in python, and uses xpath and
[mercator.py](https://github.com/hrldcpr/mercator.py).

It first finds all the paths that have a “location” attribute – those
are my reference points. It then finds the image coordinates, and the
world coordinates. The script will also extract extract locations of
all the data points, by finding paths that have the fill property to
look for. Note how XPath (a query language to select nodes in xml
documents) makes this really easy.

The script will then project the lat/lng points into the Mercator
projection, and find a least square best fit for a affine
transformation matrix between the image coordinates and the world
coordinates (in Mercator space). The data points will be transformed
to world coordinates using this transformation and unprojected to get
the lat/lng values.

The script prints the data values (lat,lng,data) as a csv on
stdout. The errors (in meters) of the reference points will be printed
on screen, to give an idea how good the transformation is.

Note that for this particular data source, the points are very
approximate in any case. But the match appears to be pretty good. The
mean error on the reference points itself is about 72m, the match on
the final result looks a bit better than that.

<img style="width: 100%; display:block; margin-left:auto; margin-right: auto" src="{filename}/images/extract-pdf/4finalingoogle.png">

The result csv files:
[Montreal](http://www.catbus.ca/devblog/wp-content/uploads/2013/04/montrealWorkPlaces.csv),
[Ottawa](http://www.catbus.ca/devblog/wp-content/uploads/2013/04/ottawaWorkPlaces.csv).

*See my
 [updated visualization of Montreal rail stations](http://www.cat-bus.com/2016/07/walksheds-visualizedshowing-population-and-places-of-workwithin-walking-distance-of-montreal-rail-stations/),
 which now includes places of work.*
