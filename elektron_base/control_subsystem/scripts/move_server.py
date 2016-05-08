#!/usr/bin/env python
######################
## written by Wojciech Dudek
######################
__author__ = "Wojciech Dudek"

########################
# Imports
########################

# Importing services
from elektron_msgs.srv import *
from elektron_msgs.msg import obstacleData
#from rapp_api.objects import * 
#from navfn.srv import *

# Importing core system functionality
import signal
import sys, os
import rospy
import almath as m
import numpy 
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from geometry_msgs.msg import PolygonStamped, Point32, PointStamped

import tf.transformations

import motion
import threading 
import geometry_msgs
#from geometry_msgs import PoseStamped
#######################################


# Constants
# class Constants:

#	NAO_IP = "nao.local"
#	PORT = 9559

	

#######################################

class MoveElektronModule():
	""" A simple module able to react to
	sound detection events
	"""
	
	# Constructor of MoveNaoModule
	def __init__(self,name):
		print "[Move server] - Acore Move Server initialization"
		
		# Initialization of ROS node
		rospy.init_node('acore_move')
		self.moduleName = name
		
		# Initialization of Naoqi modules and ROS services
		self.checkSubsystems()
		self.setVariables()

		self.openServices()


		print "[Move server] - Waits for clients ..."
				
	# Initialization of Naoqi modules
	def checkSubsystems(self):
		print "[Move server] - Checking existance of virtual receptors and effectors"

	# Setting variables
	def setVariables(self):
		print "[Move server] - Setting variables"
		self.MoveIsFailed = False
		self.GP_seq = -1
		self.tl = tf.TransformListener(True, rospy.Duration(5.0))
		self.sub_obstacle = None

	def openServices(self):
		try:
			print "[Move server] - setting services"
			print "[Move server] - service - [rapp_moveAlongPath]"
			self.service_map = rospy.Service('rapp_moveAlongPath', MoveAlongPath, self.handle_rapp_MoveAlongPath)
		except Exception, ex_map:
			print "[Move server] - Exception %s" % str(ex_map)
		try:
			print "[Move server] - service - [rapp_moveTo]"
			self.service_mt = rospy.Service('rapp_moveTo', MoveTo, self.handle_rapp_moveTo)
		except Exception, ex_mt:
			print "[Move server] - Exception %s" % str(ex_mt)
		try:
			print "[Move server] - service - [rapp_moveVel]"
			self.service_mv = rospy.Service('rapp_moveVel', MoveVel, self.handle_rapp_moveVel)
		except Exception, ex_mv:
			print "[Move server] - Exception %s" % str(ex_mv)
		try:
			print "[Move server] - service - [rapp_moveStop]"
			self.service_ms = rospy.Service('rapp_moveStop', MoveStop, self.handle_rapp_moveStop)
		except Exception, ex_ms:
			print "[Move server] - Exception %s" % str(ex_ms)	
		try:
			print "[Move server] - service - [rapp_moveJoint]"
			self.service_mj = rospy.Service('rapp_moveJoint', MoveJoint, self.handle_rapp_moveJoint)
		except Exception, ex_mj:
			print "[Move server] - Exception %s" % str(ex_mj)	
		try:
			print "[Move server] - service - [rapp_takePredefinedPosture]"
			self.service_takePosture = rospy.Service('rapp_takePredefinedPosture', TakePredefinedPosture, self.handle_rapp_takePredefinedPosture)
		except Exception, ex_takePosture:
			print "[Move server] - Exception %s" % str(ex_takePosture)
		try:
			print "[Move server] - service - [rapp_lookAtPoint]"
			self.service_lookAt = rospy.Service('rapp_lookAtPoint', LookAtPoint, self.handle_rapp_lookAtPoint)
		except Exception, ex_lookAt:
			print "[Move server] - Exception %s" % str(ex_lookAt)


	# NAOqi Event subscribtion
	def subscribeToEvents(self):
		#self.prox_memory.subscribeToEvent("ALMotion/Safety/MoveFailed", self.moduleName, "MoveCallback")
		#self.prox_memory.subscribeToEvent("LeftBumperPressed", self.moduleName, "LeftBumperPressed")
		#self.prox_memory.subscribeToEvent("RightBumperPressed", self.moduleName, "RightBumperPressed")
		#self.avoide_ID = 0
		#self.proxy_sonar.subscribe("obstacleAvoidance")
		#self.prox_memory.subscribeToEvent("Navigation/AvoidanceNavigator/ObstacleDetected", self.moduleName, "ObstacleCallback")
	# Initialization of ROS services
		print "subscribing to events"

	def getch(self):
		import sys, tty, termios
		fd = sys.stdin.fileno()
		old = termios.tcgetattr(fd)
		try:
			tty.setraw(fd)
			return sys.stdin.read(1)
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old)
#
#
#   Interfaces to virtual effector
#
#
	def rapp_move_vel_interface(self,x,theta):
		moveVel = rospy.ServiceProxy('moveVel', MoveVel)
		resp1 = moveVel(x,theta)
		return resp1.status

	def rapp_take_predefined_posture_interface(self,pose):
		takePosture = rospy.ServiceProxy('takePredefinedPosture', TakePredefinedPosture)
		resp1 = takePosture(pose,speed)
		return resp1.status

	def rapp_move_joint_interface(self,joints, angles):
		#self.unsubscribeToObstacle()
		moveJoint = rospy.ServiceProxy('moveJoint', MoveJoint)
		resp1 = moveJoint(joints, angles,0)
		return resp1.status

	def rapp_stop_move_interface(self):
		#self.unsubscribeToObstacle()
		moveStop = rospy.ServiceProxy('moveStop', MoveStop)
		resp1 = moveStop()
		return resp1.status
#
#
#   Interfaces to virtual receptor ---- TO DO
#
#
	def subscribeToObstacle(self):
		self.sub_obstacle = rospy.Subscriber("/obstacleDetectorState", obstacleData , self.detectObstacle)

	def unsubscribeToObstacle(self):
		self.sub_obstacle.unregister()
		self.sub_obstacle = None

	def isSubscribedToObstacle(self):
		if self.sub_obstacle is None:
			return False
		else:
			return True
####
##  SERVECE HANDLERS
####

	def handle_rapp_moveTo(self,req):
		try:
			if(self.tl.canTransform("map", "base_link", rospy.Time())):
				self.subscribeToObstacle()

				pose_req = geometry_msgs.PoseStamped()
				pose_req.header.frame_id = "base_link"
				pose_req.pose.position.x = req.x
				pose_req.pose.position.y = req.y
				pose_req.pose.position.z = req.z
				pose_req.pose.orientation = tf.transformations.quaternion_from_euler(0,0,req.theta)

				pose_in_map = tf.transformPose("map", pose_req)
				path = [pose_in_map]
				self.followPath(path)

				self.unsubscribeToObstacle()

				status = resp
			else:
				status = True
				print "[MoveTo server] - cannot transform robot frame to global frame"

		except Exception, ex:
			print "[MoveTo server] - Exception %s" % str(ex)
			status = True
		return MoveToResponse(status)	

	def handle_rapp_MoveAlongPath(self,req):

		self.move_is_finished = False
		self.path_is_finished = False
		self.kill_thread_followPath = False
		self.obstacle_detected = False

		self.followPath_flag = 'empty'
		rate_mainThread = rospy.Rate(1)

		#self.rapp_take_predefined_posture_interface('StandInit',0.3)
		
		self.subscribeToObstacle()
		
		pathFollowingStatus = self.followPath(req.poses)
		
		self.unsubscribeToObstacle()

		if pathFollowingStatus == "finished":
			status = False
		elif pathFollowingStatus == "transformation error":
			print "Transformation error!!!!!!!!!!"
			status = True			
		else:
			print "BUG BUG BUG BUG BUG BUG BUG BUG \n BUG BUG BUG BUG BUG BUG"
			status = True

		return MoveAlongPathResponse(status)

	def detectObstacle(self,msg):
		# while (self.path_is_finished != True): 
		# sonar data = [right_dist, left_dist]
		sum_data = 0
		i = 0

		if (msg.RightBumper == 1):
			#self.unsubscribeToObstacle()
			self.obstacle_detected = True
			self.kill_thread_followPath = True
			self.rapp_stop_move_interface()

			print "Obstacle detected by RIGHT BUMPER " 
		elif ( msg.LeftBumper==1):
			#self.unsubscribeToObstacle()
			self.obstacle_detected = True
			self.kill_thread_followPath = True
			self.rapp_stop_move_interface()
			print "Obstacle detected by LEFT BUMPER " 



	def plannPath(self,req):
		robotCurrentPosition = [req.start_x,req.start_y,req.start_theta]#self.getRobotCurrentPosition()
		start = PoseStamped()
		goal = PoseStamped()
		start.header.seq = 0
		goal.header.seq = 0
		start.header.stamp = rospy.Time.now()
		goal.header.stamp = rospy.Time.now()
		start.header.frame_id = "/map"
		goal.header.frame_id = "/map"
		start.pose.position.x = req.start_x#robotCurrentPosition[0][0]
		start.pose.position.y = req.start_y#robotCurrentPosition[0][1]
		start.pose.position.z = 0#robotCurrentPosition[0][2]
		start_orientation_quaternion = tf.transformations.quaternion_from_euler(0,0,req.start_theta) 

		start.pose.orientation.x = start_orientation_quaternion[0]
		start.pose.orientation.y = start_orientation_quaternion[1]
		start.pose.orientation.z = start_orientation_quaternion[2]
		start.pose.orientation.w = start_orientation_quaternion[3]
		goal.pose.position.x = req.finish_x
		goal.pose.position.y = req.finish_y
		goal.pose.position.z = 0
		goal_orientation_quaternion = tf.transformations.quaternion_from_euler(0,0,req.finish_theta) 
		goal.pose.orientation.x = goal_orientation_quaternion[0]
		goal.pose.orientation.y = goal_orientation_quaternion[1]
		goal.pose.orientation.z = goal_orientation_quaternion[2]
		goal.pose.orientation.w = goal_orientation_quaternion[3]
		print "tu jest start \n",start
		print "tu jest goal \n",goal
		path = numpy.array(PoseStamped())
		print "sdsanaskd"
		plan_path = rospy.ServiceProxy('/global_planner/make_plan', MakeNavPlan)
		print "okmpmmlkmvxc ssdf "
		path_resp = plan_path(start,goal)
		print "response:", path_resp.path
		print type(path_resp)
		return PlannPathResponse(path_resp.plan_found,path_resp.error_message, path_resp.path)

	def followPath(self,path):			
		status = "start"
		for i in range(int(numpy.ceil(len(path)/(20)))+1):
		#int(numpy.floor(len(path.path)/200))+1):
			print "i= ",i
			print "liczba punktow: \n", len(path)
			rospy.sleep(3)
			robotCurrentPosition = self.getRobotCurrentPosition()
			if (len(robotCurrentPosition) == 2):
				robot_orientation_euler = tf.transformations.euler_from_quaternion(robotCurrentPosition[1])
				if (len(path)-(i+1)*20<0.1):
					point_number = len(path)-1
				else:
					point_number = (i+1)*20


				nextPose = path[point_number]
				nextRotation = [nextPose.pose.orientation.x,nextPose.pose.orientation.y,nextPose.pose.orientation.z,nextPose.pose.orientation.w]
				nextPoseOrientationZ = tf.transformations.euler_from_quaternion(nextRotation)[2]#.x,nextPose.pose.orientation.y,nextPose.pose.orientation.z,nextPose.pose.orientation.w)[2]
				print "[Path tracker] - getting to next point:\n ", point_number," / ", (len(path)-1)
				print "start:\n ",robotCurrentPosition[0][0],robotCurrentPosition[0][1]
				print "finish:\n",nextPose.pose.position.x,nextPose.pose.position.y

				x_A = robotCurrentPosition[0][0]
				y_A = robotCurrentPosition[0][1]
				robot_orientation_euler = tf.transformations.euler_from_quaternion(robotCurrentPosition[1])
				gamma = robot_orientation_euler[2]
				x_B = nextPose.pose.position.x
				y_B = nextPose.pose.position.y
				AB = numpy.sqrt((x_A-x_B)*(x_A-x_B)+(y_A-y_B)*(y_A-y_B))
				nextPoseOrientationZ = tf.transformations.euler_from_quaternion(nextRotation)[2]#.x,nextPose.pose.orientation.y,nextPose.pose.orientation.z,nextPose.pose.orientation.w)[2]

				alpha = numpy.arctan2(y_B-y_A,x_B-x_A)
				#dist_Nao_trajectory = numpy.sqrt(()*()+()*())
				print "gamma|alpha\n", gamma," | ",alpha
				print "gamma|alpha", gamma," | ",nextPoseOrientationZ
				if abs(gamma)> abs(alpha):
				 	theta = -1*(gamma - alpha)
				elif abs(gamma)< abs(alpha):
					theta = (alpha - gamma)
				else:
					theta =0
				if abs(theta) > 3.14:
					print"\n theta > 3.14\n"
					theta = theta-(numpy.sign(theta)*2*numpy.pi)
				print "nawrotka na AB"
				print "theta= ",theta
				#if abs(theta) > 0.15:
				# check if next point is not too close to current robot pose
				#                 rotation more then 20 deg and goal distance more then 0.08 m || next pose is the goal 
				should_move = (abs(theta) > 20*numpy.pi/180 and AB > 0.08) or (point_number == len(path)-1)
				if (should_move):
					# rotate with velocity = 0.4 rad/sec 
					thetaTime = abs(theta)/0.4
					resp = self.rapp_move_vel_interface(0,0.4*numpy.sign(theta))
					#self.proxy_motion.move(0,0,0.3*numpy.sign(theta))
					
					#while bool(resp):
						
					thetaTime_now = 0
					while (thetaTime-thetaTime_now)>0:
						if self.obstacle_detected == True:
							status = "obstacle"
							print "AAAAAAAAAAAA"
							break	
						rospy.sleep(0.1)
						
						thetaTime_now = thetaTime_now + 0.1
					self.rapp_stop_move_interface()
					# move forward with velocity - 0.08 m/s
					print "pojscie na AB"
					move_X_time = AB/0.08
					if self.obstacle_detected == False:
						resp = self.rapp_move_vel_interface(0.08,0)
			
						move_X_time_now = 0
						while (move_X_time-move_X_time_now)>0:
							if self.obstacle_detected == True:
								status = "obstacle"
								print "BBBBBB"
								break	
							rospy.sleep(0.1)
							
							move_X_time_now = move_X_time_now + 0.1
						
						self.rapp_stop_move_interface()
					# if an obstacle was detected during movement to this point break path following and return status
					if self.obstacle_detected == True:
						print "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"
						return status
			else:
				print "can't transform base_link to map frame" 
				status = "transformation error"
				return status
		# if an obstacle was detected break path following and return status
		if self.obstacle_detected == True:
			print "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"
			return status
		# if at goal position, rotate to the goal orientation
		else:
			print "nawrotka na kierunek koncowy"
			robotCurrentPosition = self.getRobotCurrentPosition()
			robot_orientation_euler = tf.transformations.euler_from_quaternion(robotCurrentPosition[1])
			print "last point orientation: \n", nextPoseOrientationZ
			theta2 = nextPoseOrientationZ - robot_orientation_euler[2]
			if abs(theta2) > 3.14:
				print"\n theta > 3.14\n"
				theta2 = theta2-(numpy.sign(theta2)*2*numpy.pi)

			# rotate with velocity = 0.4 rad/sec 
			theta2_Time = abs(theta2)/0.4
			
			resp = self.rapp_move_vel_interface(0,0.4*numpy.sign(theta2))
		
			thetaTime_now = 0
			while (theta2_Time-thetaTime_now)>0:
				if self.obstacle_detected == True:
					status = "obstacle"
					break	
				rospy.sleep(0.1)
				
				thetaTime_now = thetaTime_now + 0.1
			self.rapp_stop_move_interface()

		if status == "obstacle":
			return status
		else:
			status = "finished"
			return status
	# def followPath2(self,path):			
	# 	status = "start"
	# 	for i in range(int(numpy.ceil(len(path)/(20)))+1):
	# 	#int(numpy.floor(len(path.path)/200))+1):
	# 		print "i= ",i
	# 		print "liczba punktow: \n", len(path)
	# 		rospy.sleep(3)
	# 		robotCurrentPosition = self.getRobotCurrentPosition()
	# 		robot_orientation_euler = tf.transformations.euler_from_quaternion(robotCurrentPosition[1])
	# 		if (len(path)-(i+1)*20<0.1):
	# 			point_number = len(path)-1
	# 		else:
	# 			point_number = (i+1)*20


	# 		nextPose = path[point_number]
	# 		nextRotation = [nextPose.pose.orientation.x,nextPose.pose.orientation.y,nextPose.pose.orientation.z,nextPose.pose.orientation.w]
	# 		nextPoseOrientationZ = tf.transformations.euler_from_quaternion(nextRotation)[2]#.x,nextPose.pose.orientation.y,nextPose.pose.orientation.z,nextPose.pose.orientation.w)[2]
	# 		print "[Path tracker] - getting to next point:\n ", point_number," / ", (len(path)-1)
	# 		print "start:\n ",robotCurrentPosition[0][0],robotCurrentPosition[0][1]
	# 		print "finish:\n",nextPose.pose.position.x,nextPose.pose.position.y

	# 		x_A = robotCurrentPosition[0][0]
	# 		y_A = robotCurrentPosition[0][1]
	# 		robot_orientation_euler = tf.transformations.euler_from_quaternion(robotCurrentPosition[1])
	# 		gamma = robot_orientation_euler[2]
	# 		x_B = nextPose.pose.position.x
	# 		y_B = nextPose.pose.position.y
	# 		AB = numpy.sqrt((x_A-x_B)*(x_A-x_B)+(y_A-y_B)*(y_A-y_B))
	# 		nextPoseOrientationZ = tf.transformations.euler_from_quaternion(nextRotation)[2]#.x,nextPose.pose.orientation.y,nextPose.pose.orientation.z,nextPose.pose.orientation.w)[2]
	# 		nextPose_POSE = PoseStamped()
	# 		cos = PoseStamped()
	# 		nextPose_POSE.header.frame_id = "map"
	# 		nextPose_POSE.header.stamp = self.tl.getLatestCommonTime("map","base_link")
	# 		print "time: ",self.tl.getLatestCommonTime("map","base_link")
	# 		nextPose_POSE = nextPose
	# 		# nextPose_POSE.pose.position.y = robotCurrentPosition[0][1]
	# 		# nextPose_POSE.pose.position.z = robotCurrentPosition[0][2]
	# 		# nextPose_POSE.pose.orientation.x = robotCurrentPosition[1][0]
	# 		# nextPose_POSE.pose.orientation.y = robotCurrentPosition[1][1]
	# 		# nextPose_POSE.pose.orientation.z = robotCurrentPosition[1][2]
	# 		# nextPose_POSE.pose.orientation.w = robotCurrentPosition[1][3]
	# 		# while not self.tl.canTransform("map","base_link",rospy.Time.now()):
	# 		# 	rospy.sleep(1)
	# 		if self.tl.canTransform("map","base_link",self.tl.getLatestCommonTime("map","base_link")):
	# 			#torso_position = self.tl.lookupTransform("map","base_link",rospy.Time())
	# 			#print numpy.dot(torso_position,nextPose_POSE)
	# 			#cos.setData(torso_position*nextPose_POSE)

	# 			#cos = self.tl.transformPose("base_link",nextPose_POSE)
	# 			#print "cos: ", cos  #"ekfpose_type is: ",type(torso_position),": \n",torso_position
	# 		#print "ekf_orientation_type is: ",type(ekf_rotation),": \n",ekf_rotation

	# 			nextPose_matrix = [[np.cos(nextPoseOrientationZ), np.sin(nextPoseOrientationZ),0,nextPose.pose.position.x],
	# 							[-np.sin(nextPoseOrientationZ), np.cos(nextPoseOrientationZ),0,nextPose.pose.position.y],
	# 							[0,0,1,0],
	# 							[0,0,0,1]]
	# 		#np.dot()
	# 		print "ZONG"
	# 		#self.rapp_move_to_interface(x_A-x_B,y_A-y_B,-(nextPoseOrientationZ-robot_orientation_euler[2]))
	# 	# 	alpha = numpy.arctan2(y_B-y_A,x_B-x_A)
	# 	# 	#dist_Nao_trajectory = numpy.sqrt(()*()+()*())
	# 	# 	print "gamma|alpha\n", gamma," | ",alpha
	# 	# 	print "gamma|alpha", gamma," | ",nextPoseOrientationZ
	# 	# 	if abs(gamma)> abs(alpha):
	# 	# 	 	theta = -1*(gamma - alpha)
	# 	# 	elif abs(gamma)< abs(alpha):
	# 	# 		theta = (alpha - gamma)
	# 	# 	else:
	# 	# 		theta =0
	# 	# 	if abs(theta) > 3.14:
	# 	# 		print"\n theta > 3.14\n"
	# 	# 		theta = theta-(numpy.sign(theta)*2*numpy.pi)
	# 	# 	print "nawrotka na AB"
	# 	# 	print "theta= ",theta
	# 	# 	#if abs(theta) > 0.15:
	# 	# 	if (abs(theta) > 20*numpy.pi/180 and AB > 0.08) or (point_number == len(path)-1):
	# 	# 		thetaTime = abs(theta)/0.3
	# 	# 		resp = self.rapp_move_vel_interface(0,0,0.3*numpy.sign(theta))
	# 	# 		#self.proxy_motion.move(0,0,0.3*numpy.sign(theta))
	# 	# 		while not bool(resp):
	# 	# 			rospy.sleep(0.1)
	# 	# 			pass
	# 	# 		thetaTime_now = 0
	# 	# 		while (thetaTime-thetaTime_now)>0:
	# 	# 			if self.obstacle_detected == True:
	# 	# 				status = "obstacle"
	# 	# 				print "AAAAAAAAAAAA"
	# 	# 				break	
	# 	# 			rospy.sleep(0.1)
					
	# 	# 			thetaTime_now = thetaTime_now + 0.1
	# 	# 	self.rapp_stop_move_interface()
	# 	# 			#self.getch() 
	# 	# 	print "pojscie na AB"
	# 	# 	move_X_time = AB/0.05
	# 	# 	#self.proxy_motion.move(0.03,0,0)
	# 	# 	if self.obstacle_detected == False:
	# 	# 		resp = self.rapp_move_vel_interface(0.05,0,0)
	# 	# 		# while not bool(resp):
	# 	# 		# 	rospy.sleep(0.1)
	# 	# 		# 	pass

	# 	# 		print "po ruchu"

	# 	# 		move_X_time_now = 0
	# 	# 		while (move_X_time-move_X_time_now)>0:
	# 	# 			if self.obstacle_detected == True:
	# 	# 				status = "obstacle"
	# 	# 				print "BBBBBB"
	# 	# 				break	
	# 	# 			rospy.sleep(0.1)
					
	# 	# 			move_X_time_now = move_X_time_now + 0.1
				
	# 	# 		self.rapp_stop_move_interface()
	# 	# 	#self.getch() 

	# 	# 	# print "nawrotka na kierunek B"
	# 	# 	# theta2 = nextPoseOrientationZ - alpha
	# 	# 	# theta2_Time = abs(theta2)/0.2
	# 	# 	# self.proxy_motion.post.move(0,0,0.2*numpy.sign(theta2))
	# 	# 	# rospy.sleep(theta2_Time)
	# 	# 	if self.obstacle_detected == True:
	# 	# 		print "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"

	# 	# 		return status
	# 	# if self.obstacle_detected == True:
	# 	# 	print "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"

	# 	# 	return status
	# 	# else:
	# 	# 	print "nawrotka na kierunek koncowy"
	# 	# 	robotCurrentPosition = self.getRobotCurrentPosition()
	# 	# 	robot_orientation_euler = tf.transformations.euler_from_quaternion(robotCurrentPosition[1])
	# 	# 	print "last point orientation: \n", nextPoseOrientationZ
	# 	# 	theta2 = nextPoseOrientationZ - robot_orientation_euler[2]
	# 	# 	if abs(theta2) > 3.14:
	# 	# 		print"\n theta > 3.14\n"
	# 	# 		theta2 = theta2-(numpy.sign(theta2)*2*numpy.pi)

	# 	# 	theta2_Time = abs(theta2)/0.2
			
	# 	# 	resp = self.rapp_move_vel_interface(0,0,0.2*numpy.sign(theta2))
	# 	# 	while not bool(resp):
	# 	# 		rospy.sleep(0.1)
	# 	# 		pass			
	# 	# 	thetaTime_now = 0
	# 	# 	while (theta2_Time-thetaTime_now)>0:
	# 	# 		if self.obstacle_detected == True:
	# 	# 			status = "obstacle"
	# 	# 			break	
	# 	# 		rospy.sleep(0.1)
				
	# 	# 		thetaTime_now = thetaTime_now + 0.1
	# 	# 	self.rapp_stop_move_interface()

	# 	if status == "obstacle":
	# 		return status
	# 	else:
	# 		status = "finished"
	# 		return status
	def getRobotCurrentPosition(self):
		if self.tl.canTransform("map","base_link",rospy.Time()):
			robot_pose = self.tl.lookupTransform("map","base_link",rospy.Time())
			robot_euler = tf.transformations.euler_from_quaternion(robot_pose[1])
		# ekf_euler - orientation from EKF
		# robot_euler - orientation from Odometry
			quaternion_to_publish = tf.transformations.quaternion_from_euler(robot_euler[0],robot_euler[1],robot_euler[2])
			robot_position = [[robot_pose[0][0],robot_pose[0][1],robot_pose[0][2]],[quaternion_to_publish[0],quaternion_to_publish[1],quaternion_to_publish[2],quaternion_to_publish[3]]] #torso_position[1][0],torso_position[1][1],torso_position[1][2]]] 
		#print "nao position",(nao_position)
			return robot_position
		else:
			print "can't transform base_link to map frame" 
			robot_position = []
			return robot_position
	def getCameraCurrentPosition(self):
		if self.tl.canTransform("map","rgb_head",rospy.Time()):
			camera_position = self.tl.lookupTransform("map","rgb_head",rospy.Time())
			return camera_position
		else:
			print "can't transform rgb_head to map frame" 

	def handle_rapp_moveVel(self,req):

		X = req.velocity_x
		Theta = req.velocity_theta
		
		self.subscribeToObstacle()
		try:
			self.rapp_move_vel_interface(X, Theta)
			status = False
		except Exception, ex:
			print "[Move server] - Exception in rapp_moveVel service handling: \n %s" % str(ex)
			status = True

		return MoveVelResponse(status)	


	def handle_rapp_moveJoint(self,req):
		try:
			status = self.rapp_move_joint_interface(req.joint_name,req.joint_angle)
		except Exception, ex:
			print "[Move server] - Exception in rapp_moveJoint service handling: \n %s" % str(ex)
			status = True
		return MoveJointResponse(status)

	def handle_rapp_moveStop(self,req):
		try:
			status = self.rapp_stop_move_interface()
			self.unsubscribeToObstacle()
		except Exception, ex:
			print "[Move server] - Exception in rapp_moveStop service handling: \n %s" % str(ex)
			status = True
		return MoveStopResponse(status)

	def handle_rapp_takePredefinedPosture(self,req):
		try:
			status = self.rapp_take_predefined_posture_interface(req.pose)
		except Exception, ex:
			status = True
			print "[Move server] - Exception %s" % str(ex)
		return TakePredefinedPostureResponse(status)	

	def compute_turn_head_angles(self, point):
		pointX = point[0]
		pointY = point[1]
		pointZ = point[2]
		dest_point = PointStamped()
		dest_point.header.frame_id = "map"
		dest_point.point.x = point[0]
		dest_point.point.y = point[1]
		dest_point.point.z = point[2]

		if(self.tl.canTransform("head_pitch_fixed","rgb_head", rospy.Time()) and self.tl.canTransform("head_pitch_revolute","rgb_head", rospy.Time()) and self.tl.canTransform("map","head_pitch_fixed", rospy.Time()) ):

			###
			#  compute head pitch angle. Based on MMAR publication
			###
			point_in_head_pitch = tf.transformPoint("head_pitch_fixed", dest_point)

			camera_in_fixed_head_pitch_transform = self.tl.lookupTransform("head_pitch_fixed","rgb_head",rospy.Time())
			camera_in_revolute_head_pitch_transform = self.tl.lookupTransform("head_pitch_revolute","rgb_head",rospy.Time())

			D = numpy.sqrt(camera_in_fixed_head_pitch_transform[0][0]*camera_in_fixed_head_pitch_transform[0][0]+camera_in_fixed_head_pitch_transform[0][2]*camera_in_fixed_head_pitch_transform[0][2]) 
			C = numpy.sqrt(point_in_head.point.x*point_in_head.point.x + point_in_head.point.z*point_in_head.point.z)
			gamma = numpy.arctan(camera_in_revolute_head_pitch_transform[0][2]/camera_in_revolute_head_pitch_transform[0][0])
			beta = 180 - gamma
			sin_sigma = (D/C) * numpy.sin(beta)
			alpha = numpy.arctan2(point_in_head.point.z, point_in_head.point.x) + numpy.arctan2(numpy.sin(sigma),numpy.sqrt(1-sin_sigma*sin_sigma))
			head_pitch = alpha + beta + gamma - 270*numpy.pi/180


			###
			#  compute head yaw angle. Based on MMAR publication
			###
			point_in_head_yaw = tf.transformPoint("head_yaw_fixed", dest_point)

			head_yaw = numpy.arctan2(point_in_head_yaw[0][1], point_in_head_yaw[0][0])




			# nao_position = self.getRobotCurrentPosition()
			# robot_orientation_euler = tf.transformations.euler_from_quaternion(nao_position[1])

			# camera_in_fixed_head_pitch_transform = self.tl.lookupTransform("base_link","rgb_head",rospy.Time())
			# camera_in_Map_transform = self.tl.lookupTransform("map","rgb_head",rospy.Time())
			# camera_Map_orientation_euler = tf.transformations.euler_from_quaternion(camera_in_Map_transform[1])

			# camera_in_robot_orientation_euler = tf.transformations.euler_from_quaternion(camera_in_fixed_head_pitch_transform[1])

			# dist2D = numpy.sqrt((pointX - camera_in_Map_transform[0][0])*(pointX - camera_in_Map_transform[0][0])+(pointY - camera_in_Map_transform[0][1])*(pointY - camera_in_Map_transform[0][1]))
			# #    *  - point
			# #    |  }
			# #    |  }  h = pointZ - NaoCamera
			# #    o    - Nao camera
			# h = pointZ - camera_in_Map_transform[0][2]#camera_position[2]-nao_position[0][2]


			# gamma = camera_Map_orientation_euler[2]
			# alpha = numpy.arctan2(pointY-camera_in_Map_transform[0][1],pointX-camera_in_Map_transform[0][0])
			# print "gamma = ",gamma, "alpha = ",alpha
			# if abs(gamma)> abs(alpha):
			#  	theta = -1*(gamma - alpha)
			# elif abs(gamma)< abs(alpha):
			# 	theta = (alpha - gamma)
			# else:
			# 	theta =0
			# if abs(theta) > 3.14:
			# 	print"\n theta > 3.14\n"
			# 	theta = theta-(numpy.sign(theta)*2*numpy.pi)
			# print "theta = ", theta
			# turn_camera_yaw = theta + camera_in_robot_orientation_euler[2]
			# turn_camera_pitch = -numpy.arctan(h/dist2D) - robot_orientation_euler[1]

			turnHeadAngles = [head_yaw,head_pitch]
			return turnHeadAngles
		else:
			turnHeadAngles = []
			print "[Cannot calculate turn head angles] - cannot transform frames"
			return turnHeadAngles



	def handle_rapp_lookAtPoint(self,req):
		pointX = req.pointX
		pointY = req.pointY
		pointZ = req.pointZ

		turnHeadAngles = self.compute_turn_head_angles([pointX,pointY,pointZ])
		if (len(turnHeadAngles) == 2):
			head_yaw = turnHeadAngles[0]
			head_pitch = turnHeadAngles[1]
			#define ranges  YAW      min        max
			range_matrix_yaw = [-numpy.pi/2,numpy.pi/2]
			#define ranges  PITCH      min        max
			range_matrix_pitch = [-numpy.pi/2,numpy.pi/2]

			#check if pitch component can be reached by robot
			if not(head_pitch > range_matrix_pitch[0] and head_pitch < range_matrix_pitch[1]):
				print "Robot cannot reach the pitch angle"
				status = True
				return LookAtPointResponse(status)	
			#check if robot has to turn around to reach the point
			if abs(head_yaw) < abs(range_matrix_yaw[0]):
				canLookAtPoint_yaw = True
			else:
				canLookAtPoint_yaw = False

			i=1
			#search the matrix for pitch boundaries for the desired head yaw position 
			while i <= 6 :
				if abs(head_yaw) > abs(range_matrix[i*3]) and canLookAtPoint_yaw:
					head_pitch_max = range_matrix[(i-1)*3+2]
					head_pitch_min = range_matrix[(i-1)*3+1]
					break
				i+=1			


				# Robot can reach head_yaw and head_pitch
			if (head_pitch > range_matrix_pitch[0] and head_pitch < range_matrix_pitch[1] and canLookAtPoint_yaw):

				self.rapp_move_joint_interface(["Head"],[head_yaw,head_pitch])
				status = False

				# Robot need rotate to be ahead of the point in yaw direction. Then he will look at it
			else:

				###
				#  compute robot yaw angle. Based on MMAR publication
				###
				dest_point = PointStamped()
				dest_point.header.frame_id = "map"
				dest_point.point.x = pointX
				dest_point.point.y = pointY
				dest_point.point.z = pointZ
				point_in_robot = tf.transformPoint("base_link", dest_point)

				robot_yaw = numpy.arctan2(point_in_robot[0][1], point_in_robot[0][0])
				
				thetaTime = abs(robot_yaw)/0.4
				req_vel = elektron_msgs.MoveVelRequest()
				req_vel.velocity_x = 0
				req_vel.velocity_y = 0
				req_vel.velocity_theta = 0.4*numpy.sign(robot_yaw)
				moveVel_trigger = self.handle_rapp_moveVel(req_vel)

				rospy.sleep(thetaTime)
				# req_stop = elektron_msgs.MoveStopRequest()
				self.handle_rapp_moveStop()
				
				turnHeadAngles = self.compute_turn_head_angles([pointX,pointY,pointZ])	
				head_yaw = turnHeadAngles[0]
				head_pitch = turnHeadAngles[1]

				status = self.rapp_move_joint_interface(["Head"],[head_yaw,head_pitch])
			return LookAtPointResponse(status)	
		else:
			status = True	
			print "[Cannot calculate turn head angles] - cannot transform frames"
			return LookAtPointResponse(status)				

# Testng SIGINT signal handler
def signal_handler(signal, frame):
	print "[Move server] - signal SIGINT caught"
	print "[Move server] - system exits"
	sys.exit(0)

def main():
	""" Main entry point
		"""
	try:
		signal.signal(signal.SIGINT, signal_handler)
		print "[Move server] - Press Ctrl + C to exit system correctly"
		
		global NaoMove
		ElektronMove = MoveElektronModule("ElektronMove")

		rospy.spin()
	
	except (KeyboardInterrupt, SystemExit):
		print "[Move server] - SystemExit Exception caught"
		#unsubscribe()
		myBroker.shutdown()
		sys.exit(0)
		
	except Exception, ex:
		print "[Move server] - Exception caught %s" % str(ex)
		#unsubscribe()
		myBroker.shutdown()
		sys.exit(0)
		
if __name__ == "__main__":
	try:
		main()
	except Exception,e:
		print "__name__ - Error %s" % str(e)