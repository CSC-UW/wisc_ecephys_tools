#!/bin/bash


substring="preprocessing"  # Replace "your_substring" with the actual substring

echo "Renaming previous preprocesing dirs"
for directory in $(ls -r -d $1/*/); do
    dir_name="${directory%/}"  # Remove trailing slash
    if [[ -d "$directory" && "$dir_name" == *"$substring"* ]]; then
        new_name="${dir_name}.bak"
        mv "$dir_name" "$new_name"
        echo "Renamed: $dir_name --> $new_name"
    fi
done

echo ""
echo "Create dir: $1/preprocessing"
mkdir $1/preprocessing
echo ""
echo "Copy opts.yaml to preprocessing.bak"
cp $1/opts.yaml $1/preprocessing.bak
echo ""
echo "Copying peaks.npy from dir/preprocessing.bak to dir/preprocessing. "
cp $1/preprocessing.bak/peaks.npy $1/preprocessing
echo "Copying peak_locations.npy from dir/preprocessing.bak to dir/preprocessing. "
cp $1/preprocessing.bak/peak_locations.npy $1/preprocessing
echo ""
echo "Done! 'peaks.npy' and 'peak_locations.npy' were copied from previous 'preprocessing' directory..."
echo "MAKE SURE YOU DON'T MODIFY OPTION PARAMETERS ALTERING PEAK DETECTION/LOCALIZATION! (or delete newly created preprocessing dir)"
