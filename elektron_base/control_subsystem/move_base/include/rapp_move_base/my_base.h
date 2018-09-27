
#include <elektron_msgs/MoveAlongPathRequest.h>
#include <elektron_msgs/MoveAlongPathResponse.h>
#include <elektron_msgs/MoveAlongPath.h>
#include <ros/ros.h>
#include <tf/transform_listener.h>
#include <costmap_2d/costmap_2d_ros.h>
#include <dwa_local_planner/dwa_planner_ros.h>
#include <tf2_ros/transform_listener.h>

namespace rapp_move_base {

 class RappMoveBase {
    public:
      /**
       * @brief  Constructor for the actions
       * @param name The name of the action
       * @param tf A reference to a TransformListener
       */
      RappMoveBase(tf2_ros::Buffer& tfBuffer);

      /**
       * @brief  Destructor - Cleans up
       */
      virtual ~RappMoveBase();
void recoveryBehavior(bool &comp_vel_status, geometry_msgs::Twist &cmd_vel);


      void publishZeroVelocity();
      /**
       * @brief  Performs a control cycle
       * @param goal A reference to the goal to pursue
       * @param global_plan A reference to the global plan being used
       * @return True if processing of the goal is done, false otherwise
       */
      bool MoveAlongPath_handler(elektron_msgs::MoveAlongPath::Request& move_req, elektron_msgs::MoveAlongPath::Response& move_response);

private:
const std::vector<geometry_msgs::PoseStamped> *req_path;
 ros::Publisher vel_pub_;
 costmap_2d::Costmap2DROS *costmap_;
 dwa_local_planner::DWAPlannerROS *dp_;
 ros::ServiceServer moveAlongPath_srv_;
ros::NodeHandle nh_;    

};
};
