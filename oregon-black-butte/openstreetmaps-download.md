# Open Street Maps Download

You can download an SVG of the street maps using the same bounding box lat and lon used to create the STL.  

Basic instructions:

Download OSM by bounding box and create SVG
https://github.com/enzet/Roentgen

Article about: https://pythonawesome.com/a-simple-renderer-for-openstreetmap-with-python/#map-generation


Working OSM (open street map) URL for bounding box:
https://api.openstreetmap.org/api/0.6/map?bbox=44.36171176019724%2C-121.68013569742145%2C44.43009951161787%2C-121.59661098226607

For Roentgen, had to create the "maps" directory, then this call worked:


>> python roentgen.py -b " -121.68013569742145,44.36171176019724,-121.59661098226607,44.43009951161787" -o map.svg
Getting https://api.openstreetmap.org/api/0.6/map?bbox=-121.68013569742145%2C44.36171176019724%2C-121.59661098226607%2C44.43009951161787...
100 % ████████████████████▏Constructing ways
100 % ████████████████████▏Constructing nodes
100 % ████████████████████▏Drawing ways
100 % ████████████████████▏Drawing buildings
100 % ████████████████████▏Drawing nodes icons
Writing output SVG...

Notes:
* SVG includes only those elements in the bounding box, and those that cross into it.
* Significant cleanup is required to trim to the bounding box for elements that cross.
* Full download has a lot of detail.  Might only want "ways".  Not sure about nodes.
