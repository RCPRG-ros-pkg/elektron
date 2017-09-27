#!/bin/bash

export RAPP_BASE=~/rapp;

mkdir -p ~/rapp/robots/src;
cd ~/rapp/robots/src;
if [ -d "elektron" ]; then
	cd ~/rapp/robots/src/elektron;
	git pull;
else
	git clone https://github.com/rcprg-ros-pkg/elektron.git;
fi

cd ~/rapp/robots/src/elektron;
git submodule update --init --recursive elektron-simulation;
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


