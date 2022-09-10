#---------------Auto Scaling Down Instances When There Are No Running Containers---------------------
import boto3
import datetime
import math
import time


#---This method will provide the unix time once the timestamp is provided
def unix_time(time_stamp):
    return time.mktime(time_stamp.timetuple())


#---This method will scale down the cluster
#---containerInstance and container instances count is needed
def scale_down(containerInstance, container_instances_count):
    #Here "containerInstance" is an EC2 instance in the cluster
    print "\nContainer Instance ID: " + containerInstance['ec2InstanceId']
    #Check if the instance state has running task or pending tasks and number of instances in the cluster is greater than 1
    #Running task = running containers, pending taks means the containers which are in queue to run in the considering instance
    if (containerInstance['runningTasksCount'] == 0 and containerInstance['pendingTasksCount']== 0 and container_instances_count > 1):
        #registration time of the container instance
        #This means starting time on the EC2 instance
        time_reg = containerInstance['registeredAt']
     #current time of the instance
        current_time = datetime.datetime.now()#next billing hour of the instance
        #current_time - registered time give you time different. When you divide it by 60*60 you get the different in hourse
        #Eg: hours_different could be 0.5 , 1.3, 2.5 etc.
        hours_difference = (unix_time(current_time) - unix_time(time_reg))/(60*60)
        #next billing hour can be takes by registered time + round up value of the hours difference
        next_billing_hour = time_reg + datetime.timedelta(hours=math.ceil(hours_difference))print ("Next billing hour begins: %s" % next_billing_hour )
        #check if the current time greater than 45 minutes of the current billing hour
        # You can edit this by changine following 15 value by any value you like.
        #This value actually depends on the cron job
        threshold_time = next_billing_hour - datetime.timedelta(minutes=15)
        print ("Threshold time to kill: %s" % threshold_time )
        print ("Current time: %s" % current_time )
        #check if the current time is less than the time to be killed the instance
        if unix_time(threshold_time) < unix_time(current_time):
            #Terminate the instance and number of available container instances would be decreased by 1
            print "Terminating instance " + containerInstance['ec2InstanceId']
            #auto scale group API called to terminate the instance by providing the instance ID
            #Desired capacity should be decrement after terminating the instance, hence ShouldDecrementDesiredCapacity=true
            asgClient.terminate_instance_in_auto_scaling_group(InstanceId=containerInstance['ec2InstanceId'], ShouldDecrementDesiredCapacity=True)
     container_instances_count -= 1
     print ("Size of the cluster after termination %s\n" %container_instances_count)
    #if there are running/pending containers inside the instances
    else :
        print ("Running Containers {} \nPending tasks {} \nCluster size {} \n ".
            format(containerInstance['runningTasksCount'],containerInstance['pendingTasksCount'],container_instances_count))#choose the aws user which to access the resources




#this account will be taken from the aws cli you have configured in your machine
session = boto3.Session(profile_name='myAccount')#ecs client and auto scaling group resource generation
ecsClient = session.client(service_name='ecs')
asgClient = session.client(service_name='autoscaling')#list container instances of the cluster


#you will have to provide the cluster name here. eg: ECS-Cluster
clusterListResp = ecsClient.list_container_instances(cluster='ECS-Cluster')#details of EC2 container instances
containerDetails = ecsClient.describe_container_instances(cluster='ECS-Cluster', containerInstances=clusterListResp['containerInstanceArns'])#Get the instances count in the cluster
container_instances_count = len(containerDetails['containerInstances'])#loop through every instances to check if it should be terminated
for containerInstance in containerDetails['containerInstances']:
    scale_down(containerInstance, container_instances_count)