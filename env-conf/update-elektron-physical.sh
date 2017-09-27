#!/bin/bash

mkdir -p ~/rapp/robots/src;
cd ~/rapp/robots/src;
if [ -d "elektron" ]; then
	cd ~/rapp/robots/src/elektron;
	git pull;
else
	git clone -b master https://github.com/rcprg-ros-pkg/elektron.git;
fi

cd ~/rapp/robots/src/elektron;
git submodule update --init --recursive elektron_base/elektron-real-effectors netusb_camera_driver;
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


