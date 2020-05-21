#!/bin/bash
ret_code=1

while [ $ret_code != 0 ]  # failed for any reason
do
    d:/Autodesk/Maya2020/bin/mayapy.exe "./datasim.py" --data data_150_tee_200515-15-31-40-slice-iterative  # --config sim_props_good_render_basic_body.json
    ret_code=$?
    echo $ret_code
done