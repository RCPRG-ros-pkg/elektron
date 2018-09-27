#include <rapp_move_base/my_base.h>

#include <elektron_msgs/MoveAlongPathRequest.h>
#include <elektron_msgs/MoveAlongPathResponse.h>
#include <elektron_msgs/MoveAlongPath.h>


int main(int argc, char** argv){
	ros::init(argc, argv, "move_base_node");
	tf2_ros::Buffer tfBuffer;
    tf2_ros::TransformListener tfListener(tfBuffer);
	tf::TransformListener tf(ros::Duration(10));

  rapp_move_base::RappMoveBase move_base( tfBuffer );

  ros::MultiThreadedSpinner s(5);
  s.spin();
   // ros::spin();

  return(0);
}
