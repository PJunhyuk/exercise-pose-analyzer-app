## Import the required modules
# Check time required
import time
time_start = time.time()

import sys
import os
import argparse as ap

import math

import imageio
from moviepy.editor import *

import numpy as np

sys.path.append(os.path.dirname(__file__) + "/../")

from scipy.misc import imread, imsave

from config import load_config
from dataset.factory import create as create_dataset
from nnet import predict
from util import visualize
from dataset.pose_dataset import data_to_input

from multiperson.detections import extract_detections
from multiperson.predict import SpatialModel, eval_graph, get_person_conf_multicut
from multiperson.visualize import PersonDraw, visualize_detections

import matplotlib.pyplot as plt

from PIL import Image, ImageDraw, ImageFont
font = ImageFont.truetype("./font/NotoSans-Bold.ttf", 12)

import random

####################

cfg = load_config("demo/pose_cfg_multi.yaml")

dataset = create_dataset(cfg)

sm = SpatialModel(cfg)
sm.load()

draw_multi = PersonDraw()

# Load and setup CNN part detector
sess, inputs, outputs = predict.setup_pose_prediction(cfg)

##########
## Get the source of video

parser = ap.ArgumentParser()
parser.add_argument('-f', "--videoFile", help="Path to Video File")
parser.add_argument('-w', "--videoWidth", help="Width of Output Video")
parser.add_argument('-o', "--videoType", help="Extension of Output Video")

args = vars(parser.parse_args())

if args["videoFile"] is not None:
    video_name = args["videoFile"]
else:
    print("You have to input videoFile name")
    sys.exit(1)
video_output_name = video_name.split('.')[0]

# Read video from file
video_name_input = 'testset/' + video_name
video = VideoFileClip(video_name_input)

print("Input video size: [" + str(video.size[0]) + ", " + str(video.size[1]) + "]")

if args["videoWidth"] is not None:
    video_width = int(args["videoWidth"])
    video = video.resize(width = video_width)
print("Changed video size: [" + str(video.size[0]) + ", " + str(video.size[1]) + "]")

if args["videoType"] is not None:
    video_type = args["videoType"]
else:
    video_type = "mp4"
print("Output video type: " + video_type)

##########
## Define some functions to mark at image

def ellipse_set(person_conf_multi, people_i, point_i):
    return (person_conf_multi[people_i][point_i][0] - point_r, person_conf_multi[people_i][point_i][1] - point_r, person_conf_multi[people_i][point_i][0] + point_r, person_conf_multi[people_i][point_i][1] + point_r)

##########

video_frame_number = int(video.duration * video.fps) ## duration: second / fps: frame per second
video_frame_ciphers = math.ceil(math.log(video_frame_number, 10)) ## ex. 720 -> 3

pose_frame_list = []

point_r = 3 # radius of points
point_min = 14 # threshold of points - If there are more than point_min points in person, we define he/she is REAL PERSON
point_num = 17 # There are 17 points in 1 person

##########

for i in range(0, video_frame_number):
    # Save i-th frame as image
    image = video.get_frame(i/video.fps)

    ##########
    ## By pose-tensorflow

    image_batch = data_to_input(image)

    # Compute prediction with the CNN
    outputs_np = sess.run(outputs, feed_dict={inputs: image_batch})
    scmap, locref, pairwise_diff = predict.extract_cnn_output(outputs_np, cfg, dataset.pairwise_stats)

    detections = extract_detections(cfg, scmap, locref, pairwise_diff)
    unLab, pos_array, unary_array, pwidx_array, pw_array = eval_graph(sm, detections)
    person_conf_multi = get_person_conf_multicut(sm, unLab, unary_array, pos_array)

    #####

    # Add library to draw image
    image_img = Image.fromarray(image)

    # Prepare saving image with points of pose
    draw = ImageDraw.Draw(image_img)

    people_num = 0

    people_num = person_conf_multi.size / (point_num * 2)
    people_num = int(people_num)

    for people_i in range(0, people_num):
        # point_color_r = random.randrange(0, 256)
        # point_color_g = random.randrange(0, 256)
        # point_color_b = random.randrange(0, 256)
        point_color_r = 255
        point_color_g = 0
        point_color_b = 0
        point_color = (point_color_r, point_color_g, point_color_b, 255)
        point_list = []
        point_count = 0
        point_i = 0 # index of points

        # To find rectangle which include that people - list of points x, y coordinates
        people_x = []
        people_y = []

        for point_i in range(0, point_num):
            if person_conf_multi[people_i][point_i][0] + person_conf_multi[people_i][point_i][1] != 0: # If coordinates of point is (0, 0) == meaningless data
                point_count = point_count + 1
                point_list.append(point_i)

        if point_count >= point_min:
            for point_i in range(0, point_num):
                if person_conf_multi[people_i][point_i][0] + person_conf_multi[people_i][point_i][1] != 0: # If coordinates of point is (0, 0) == meaningless data
                    draw.ellipse(ellipse_set(person_conf_multi, people_i, point_i), fill=point_color)
                    people_x.append(person_conf_multi[people_i][point_i][0])
                    people_y.append(person_conf_multi[people_i][point_i][1])

    draw.text((0, 0), 'Frame: ' + str(i) + '/' + str(video_frame_number), (0,0,0), font=font)
    draw.text((0, 18), 'Total time required: ' + str(round(time.time() - time_start, 1)) + 'sec', (0,0,0), font=font)

    print('Frame: ' + str(i) + "/" + str(video_frame_number))
    print('Time required: ' + str(round(time.time() - time_start, 1)) + 'sec')

    image_img_numpy = np.asarray(image_img)

    pose_frame_list.append(image_img_numpy)

video_pose = ImageSequenceClip(pose_frame_list, fps=video.fps)
video_pose.write_videofile("testset/" + video_output_name + "_pose." + video_type, fps=video.fps, progress_bar=False)

print("Time(s): " + str(time.time() - time_start))
print("Output video size: [" + str(video.size[0]) + ", " + str(video.size[1]) + "]")
