#!/bin/bash
# This script is needed to autorestart execution of simulating datapoints for a dataset in case of Maya\Qualoth hangs or crashes
# Note that it's needed to suppress Maya crash report requests 
#   * https://knowledge.autodesk.com/support/maya/troubleshooting/caas/sfdcarticles/sfdcarticles/How-to-Disable-or-Enable-Crash-Error-Reports-s.html
#   * https://forums.autodesk.com/t5/installation-licensing/disable-error-reporting/td-p/4071164 
# Use something like git bash to run this script on Win

# ensure killing is possible
# https://www.linuxjournal.com/article/10815

# Use Ctrl-C to stop this script after currently running mini-batch finishes
sigint()
{
   echo "Ctrl-C signal INT received, script ending after returning from datasim execution"
   exit 1
}
trap 'sigint'  INT

# -- Main calls --
num_samples=15
per_sample_delay=$((5*60))  # give about 5 min per sample before detecting Maya to hang
dataset=data_150_tee_200521-16-30-22
ret_code=1
while [ $ret_code != 0 ]  # failed for any reason
do
    # https://unix.stackexchange.com/questions/405337/bash-if-command-doesnt-finish-in-x-time
    # set timeout to catch hangs. Give about num_samples x 5 min for a single run
    timeout $((num_samples * per_sample_delay)) d:/Autodesk/Maya2020/bin/mayapy.exe "./datasim.py" --data $dataset --minibatch $num_samples  --config sim_props_good_render_basic_body.json
    ret_code=$?
    echo $ret_code   # if it's 124, the execution was finished by timeout
done