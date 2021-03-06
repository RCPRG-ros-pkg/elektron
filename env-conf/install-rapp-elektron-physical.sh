#!/bin/bash
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
bash install_packages.sh

mkdir -p ~/rapp/rapp-api/src ;
cd ~/rapp/rapp-api/src;

if [ -d "rapp-api" ]; then
	cd ~/rapp/rapp-api/src/rapp-api;
	git pull;
else
	git clone -b wut https://github.com/rapp-project/rapp-api.git;
fi

cd ~/rapp/rapp-api/src;

if [ -d "rapp-robots-api" ]; then
	cd ~/rapp/rapp-api/src/rapp-robots-api;
	git pull;
else
	git clone -b cpp https://github.com/rapp-project/rapp-robots-api.git;
fi

cd ~/rapp/rapp-api/src;

source /opt/ros/indigo/setup.bash;
cd ~/rapp/rapp-api;

if [ -d "install" ]; then
	catkin clean -y;
	catkin init;
	catkin config --cmake-args -DBUILD_ALL=ON;
	catkin config --install;
	catkin build;
else
	catkin init;
	catkin config --cmake-args -DBUILD_ALL=ON;
	catkin config --install;
	catkin build;
fi

mkdir -p ~/rapp/robots/src;
cd ~/rapp/robots/src;
if [ -d "elektron" ]; then
	cd ~/rapp/robots/src/elektron;
	git pull;
else
	git clone -b master https://github.com/dudekw/elektron.git;
fi

cd ~/rapp/robots/src/elektron;

git submodule update --init --recursive elektron_base/elektron-real-effectors netusb_camera_driver rapp-api-elektron elektron_apps/elektron-rapps;
source /opt/ros/indigo/setup.bash;
source ~/rapp/rapp-api/install/setup.bash;
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

