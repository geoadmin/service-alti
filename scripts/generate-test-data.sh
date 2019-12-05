#!/bin/bash

project_folder=$PWD
data_folder=/var/local/geodata/bund/swisstopo

# creating a tmp folder where we will files that need a crop or another likewise operation with gdal
tmp_dir=$(mktemp -d)

# crop a given file with gdalwarp to the extent of tile 1208-4.bt (see data/README.md)
# param $1 is source file, param $2 is destination file
function cropToTile {
  gdalwarp -s_srs EPSG:21781 -of BT -te "$3" "$1" "$2"
}

# crop matrix BT file, copy result to data/$1, and regenerate index shapefile
# $1 is the name of the matrix (dhm25_25_matrix for instance)
function transformMatrix {
  # creating folder with matrix name in tmp folder
  mkdir "$tmp_dir"/"$1"
  # copying binaryterrain file for this matrix from the EFS to the tmp folder
  cp $data_folder/"$1"/mm0001.bt "$tmp_dir"/"$1"/
  # transforming the BT file to be at the same extent as the 1208-4.bt tile (reducing drastically its size on the disk)
  if [ "$2" == 21781 ]; then
    gdal_translate -of BT -projwin 628750 176000 637500 170000 "$tmp_dir"/"$1"/mm0001.bt "$tmp_dir"/"$1"/mm0001_warp.bt
  else
    gdal_translate -of BT -projwin 2628750 1176000 2637500 1170000 "$tmp_dir"/"$1"/mm0001.bt "$tmp_dir"/"$1"/mm0001_warp.bt
  fi
  # cleaning data/ directory before copying results
  rm -f "$project_folder"/data/"$1"/mm0001.*
  # copying results in data/
  mv -f "$tmp_dir"/"$1"/mm0001_warp.bt "$tmp_dir"/"$1"/mm0001.bt
  cp "$tmp_dir"/"$1"/* "$project_folder"/data/"$1"
  # regenerating shapefile index
  cd "$project_folder"/data/"$1"/ || exit 1
  gdaltindex -t_srs EPSG:"$2" mm0001.shp mm0001.bt
}

# copy "the" tile into data/ and regenerate index shapefile
function transformTileAndIndex {
  cp $data_folder/swissalti3d/"$1"/1208-4.bt "$project_folder"/data/swissalti3d/"$1"
  # regenerating shapefile
  rm -f "$project_folder"/data/swissalti3d/"$1"/index.*
  cd "$project_folder"/data/swissalti3d/"$1"/ || exit 1
  gdaltindex index.shp 1208-4.bt
}

if [[ -d /var/local/geodata/ ]]; then

  transformMatrix dhm25_25_matrix 21781
  transformMatrix dhm25_25_matrix_lv95 2056

  transformTileAndIndex 2m
  transformTileAndIndex 2m_lv95
  transformTileAndIndex kombo_2m_dhm25
  transformTileAndIndex kombo_2m_dhm25_lv95

else
  echo "Can't create test data, folder /var/local/geodata/ not accessible on this system.";
fi

# cleaning up tmp dir created above
rm -rf "$tmp_dir"
