#!/bin/bash
RED='\033[0;31m';
YELLOW='\033[1;33m';
NC='\033[0m';

sudo sh -c '. /etc/lsb-release && echo "deb http://packages.ros.org.ros.informatik.uni-freiburg.de/ros/ubuntu $DISTRIB_CODENAME main" > /etc/apt/sources.list.d/ros-latest.list'
wget -O install_packages.sh https://raw.githubusercontent.com/rcprg-ros-pkg/elektron/kinetic/env-conf/install_packages.sh;
bash install_packages.sh

source /opt/ros/kinetic/setup.bash;
printf "${YELLOW}Do you wish to install gazebo7 from source?${NC} (y/n) \n"
read answer
if echo "$answer" | grep -iq "^y" ;then
    wget -O install_elektron_gazebo.sh https://raw.githubusercontent.com/rcprg-ros-pkg/elektron/kinetic/env-conf/install-elektron-gazebo.sh && bash install_elektron_gazebo.sh;
fi

mkdir -p ~/rapp/robots/src;
cd ~/rapp/robots/src;
if [ -d "elektron" ]; then
        cd ~/rapp/robots/src/elektron;
        git pull;
else
        git clone -b kinetic https://github.com/rcprg-ros-pkg/elektron.git;
fi

cd ~/rapp/robots/src/elektron;
touch elektron_base/elektron-real-effectors/CMakeLists.txt;
git submodule update --init --recursive elektron-simulation;
if echo "$answer" | grep -iq "^y" ;then
   input_path_to_gazebo_ws="$HOME/gazebo_ws/underlay_isolated/devel/setup.bash"
else
   printf "${YELLOW}Please enter path to workspace with gazebo7${NC} (path to setup.bash file): \n"
   read -p "" -i "$HOME/" -e input_path_to_gazebo_ws
fi

source $input_path_to_gazebo_ws;
cd ../..;

if [ -d "install" ]; then
        catkin clean -y;
        catkin init;
        catkin config --install;
        catkin build
else
        catkin init;
        catkin config --install;
        catkin build
fi

