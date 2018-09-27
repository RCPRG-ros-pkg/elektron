/*********************************************************************
*
* Software License Agreement (BSD License)
*
*  Copyright (c) 2008, Willow Garage, Inc.
*  All rights reserved.
*
*  Redistribution and use in source and binary forms, with or without
*  modification, are permitted provided that the following conditions
*  are met:
*
*   * Redistributions of source code must retain the above copyright
*     notice, this list of conditions and the following disclaimer.
*   * Redistributions in binary form must reproduce the above
*     copyright notice, this list of conditions and the following
*     disclaimer in the documentation and/or other materials provided
*     with the distribution.
*   * Neither the name of the Willow Garage nor the names of its
*     contributors may be used to endorse or promote products derived
*     from this software without specific prior written permission.
*
*  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
*  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
*  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
*  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
*  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
*  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
*  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
*  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
*  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
*  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
*  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
*  POSSIBILITY OF SUCH DAMAGE.
*
* Author: Eitan Marder-Eppstein
*         Mike Phillips (put the planner in its own thread)
*********************************************************************/
#include <rapp_move_base/my_base.h>
#include <cmath>

#include <boost/algorithm/string.hpp>
#include <boost/thread.hpp>

#include <geometry_msgs/Twist.h>
#include <elektron_msgs/MoveAlongPathRequest.h>
#include <elektron_msgs/MoveAlongPathResponse.h>
#include <elektron_msgs/MoveAlongPath.h>
#include <tf2_ros/transform_listener.h>

namespace rapp_move_base {

  RappMoveBase::RappMoveBase(tf2_ros::Buffer& tfBuffer){
    // costmap_2d::Costmap2DROS costmap("my_costmap", tf);
    // costmap.pause();
    costmap_ = new costmap_2d::Costmap2DROS("my_costmap", tfBuffer);
    costmap_->start();

    // dwa_local_planner::DWAPlannerROS dp;
    dp_ = new dwa_local_planner::DWAPlannerROS;
    dp_->initialize("my_dwa_planner", &tfBuffer, costmap_);

    ROS_INFO("STARTING MY SERVICE");
    std::string node_name = ros::this_node::getName();
    moveAlongPath_srv_ = nh_.advertiseService("rapp_moveAlongPath_ros", &RappMoveBase::MoveAlongPath_handler, this);
    vel_pub_ = nh_.advertise<geometry_msgs::Twist>(node_name+"/cmd_vel", 1);
}
void RappMoveBase::publishZeroVelocity(){
    geometry_msgs::Twist cmd_vel;
    cmd_vel.linear.x = 0.0;
    cmd_vel.linear.y = 0.0;
    cmd_vel.angular.z = 0.0;
    vel_pub_.publish(cmd_vel);
}
void RappMoveBase::recoveryBehavior(bool &comp_vel_status, geometry_msgs::Twist &cmd_vel){
    ros::Duration time_dur;
    ros::Time time_1;
    ros::Time time_2;

    while(nh_.ok())
    {
      cmd_vel.angular.z = 0.4;
      vel_pub_.publish(cmd_vel);
      costmap_->resetLayers();
      costmap_->start();
      comp_vel_status = dp_->computeVelocityCommands(cmd_vel);
      if (comp_vel_status){
        time_1 = ros::Time::now();
        while (time_dur > ros::Duration(2)){
          cmd_vel.angular.z = 0.4;
          vel_pub_.publish(cmd_vel);
          time_2 = ros::Time::now();
          time_dur = time_1 - time_2;
        }
        costmap_->resetLayers();
        costmap_->start();
        comp_vel_status = dp_->computeVelocityCommands(cmd_vel);
        if (comp_vel_status){
        //   time_1 = ros::Time::now();
        //   while (time_dur > ros::Duration(2)){
        //     cmd_vel.angular.z = 0.0;
        //     cmd_vel.linear.x = 0.05;
        //     vel_pub_.publish(cmd_vel);
        //     time_2 = ros::Time::now();
        //     time_dur = time_1 - time_2;
        //   }
        //   costmap_->resetLayers();
        //   costmap_->start();
          return;
        
        }
      }
    }
}
  bool RappMoveBase::MoveAlongPath_handler(elektron_msgs::MoveAlongPath::Request &req, elektron_msgs::MoveAlongPath::Response &resp)
  {
    costmap_->resume();

    std::vector<geometry_msgs::PoseStamped> req_path_obj;
    req_path_obj = req.poses;
    req_path = &req_path_obj;
    dp_->setPlan(req_path_obj);
    ros::Rate r(5);
    geometry_msgs::Twist cmd_vel;
    bool comp_vel_status;
    bool goal_reached_status;   
bool kp;
ros::Time last_valid_control;
ros::Time last_Invalid_control;
    while(nh_.ok())
    {
          // costmap_->updateMap();

      ROS_INFO("New velocity");
      last_valid_control = ros::Time::now();
         // boost::unique_lock<costmap_2d::Costmap2D::mutex_t> lock(*(costmap_->getCostmap()->getMutex()));
      comp_vel_status = dp_->computeVelocityCommands(cmd_vel);
      ROS_INFO("After compute");
      ROS_INFO("publish");
// if (last_valid_control - last_Invalid_control > ros::Duration(6))
//   kp = true;
      vel_pub_.publish(cmd_vel);
      ROS_INFO("published");
// if (kp){
//         last_Invalid_control = ros::Time::now();
// kp = false;
//   ros::Duration(3).sleep();
// }
      if ((!comp_vel_status )){
          ROS_INFO("Can't compute velocity");

          ROS_INFO("Running recovery behavior");
          recoveryBehavior(comp_vel_status, cmd_vel);
          //resp.status = false;
          //return false;
        }
      if(dp_->isGoalReached()){
          ROS_INFO("Goal reached");
          costmap_->pause();
          resp.status = true;
          return true;
      }
      if(!costmap_->isCurrent()){
          ROS_WARN("[%s]:Sensor data is out of date, we're not going to allow commanding of the base for safety",ros::this_node::getName().c_str());
          publishZeroVelocity();
          resp.status = false;

          return false;
      }
      r.sleep();
    }
      ROS_INFO_STREAM("N status:"<< nh_.ok());

    //wake up the planner thread so that it can exit cleanly
    // lock.lock();
    // runPlanner_ = true;
    // planner_cond_.notify_one();
    // lock.unlock();

    //if the node is killed then we'll abort and return
    //as_->setAborted(rapp_move_base_msgs::RappMoveBaseResult(), "Aborting on the goal because the node has been killed");
    costmap_->pause();

    resp.status = false;
    return false;
  }

  RappMoveBase::~RappMoveBase(){

  }

};
