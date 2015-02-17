#coding: utf-8

import os
import re
import cv2
import image_util as iu
import logging
import sys
import yaml

class InriaPersonDataSet:

    CONFIG_YAML = 'config.yml'

    def __init__(self):

        # log setting
        program = os.path.basename(sys.argv[0])
        self.logger = logging.getLogger(program)
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s')

        # load config file
        f = open(InriaPersonDataSet.CONFIG_YAML, 'r')
        self.config = yaml.load(f)
        f.close()

        # set dataset path
        self.pos_img_dir = self.config['dataset']['pos_img_dir']
        self.neg_img_dir = self.config['dataset']['neg_img_dir']
        self.annotation_dir = self.config['dataset']['annotation_dir']

        # set output path
        self.cropped_dir = self.config['output']['cropped_dir']
        self.bounding_box_out_dir = self.config['output']['bounding_box_out_dir']
        self.out_dir = self.config['output']['out_dir']

        # create output paths
        if not os.path.isdir(self.cropped_dir):
            os.mkdir(self.cropped_dir)
        if not os.path.isdir(self.bounding_box_out_dir):
            os.mkdir(self.bounding_box_out_dir)
        if not os.path.isdir(self.out_dir):
            os.mkdir(self.out_dir)

        # set array of all file names
        self.pos_img_files = [file_name for file_name in os.listdir(self.pos_img_dir) if not file_name.startswith('.')]
        self.neg_img_files = [file_name for file_name in os.listdir(self.neg_img_dir) if not file_name.startswith('.')]
        self.cropped_files = [file_name for file_name in os.listdir(self.cropped_dir) if not file_name.startswith('.')]

    def parse_annotation_file(self, img_file_name):

        # image annotation path
        annotation_path = self.annotation_dir + os.path.splitext(img_file_name)[0] + '.txt'

        # open annotation file
        f = open(annotation_path)
        lines = f.readlines()
        f.close()

        # parse annotation file
        object_list = []
        object_info = {}
        ground_truth = None
        img_size = None

        for line in lines:
            # print line,

            # get image size
            m = re.match(r'Image size \(X x Y x C\) : (\d+) x (\d+) x 3', line)
            if m:
                img_size = (int(m.group(1)), int(m.group(2)))
                # print img_size

            # get ground truth
            m = re.match(r'Objects with ground truth : (\d+)', line)
            if m:
                ground_truth = int(m.group(1))
                # print ground_truth

            if line.find('# Details for object') != -1:
                object_info = {}
                # print '# Details for object'

            # get center
            m = re.match(r'Center point on object (\d)+ "PASperson" \(X, Y\) : \((\d+), (\d+)\)', line)
            if m:
                center = (int(m.group(2)), int(m.group(3)))
                # print center
                object_info['center'] = center

            # get bounding box
            m = re.match(r'Bounding box for object (\d+) "PASperson" \(Xmin, Ymin\) - \(Xmax, Ymax\) : \((\d+), (\d+)\) - \((\d+), (\d+)\)', line)
            if m:
                bounding_box = [(int(m.group(2)), int(m.group(3))), (int(m.group(4)), int(m.group(5)))]
                # print bounding_box
                object_info['bounding_box'] = bounding_box
                object_list.append(object_info)

        # check number of objects
        if len(object_list) != ground_truth:
            Exception("parsing error: ground truth does not match with object number.")
            return None

        # create annotation info
        annotation_info = {
            'img_size': img_size,
            'ground_truth': ground_truth,
            'object_list': object_list
        }

        return annotation_info

    def draw_bounding_boxes_for_all(self):
        self.logger.info("begin drawing bounding boxes")
        for file_name in self.pos_img_files:

            # skip hidden file
            if file_name.startswith('.'):
                continue

            # draw bounding box
            self.draw_bounding_boxes_and_write_file(file_name)

    def draw_bounding_boxes_and_write_file(self, file_name):

        file_path = self.pos_img_dir + file_name
        self.logger.info("drawing bounding box: " + file_path)

        # read image
        img = cv2.imread(file_path, cv2.IMREAD_COLOR)

        # read annotation file to get annotation info
        annotation_info = self.parse_annotation_file(file_name)

        # iterate object list and draw bounding boxes
        for object_info in annotation_info['object_list']:
            bounding_box = object_info['bounding_box']
            cv2.rectangle(img, bounding_box[0], bounding_box[1], (0, 0, 255), 5)

        # output file
        cv2.imwrite(self.bounding_box_out_dir + 'b_' + file_name, img)

    def create_crop_for_all(self):
        self.logger.info("begin creating crop image")
        for file_name in self.pos_img_files:

            # skip hidden file
            if file_name.startswith('.'):
                continue

            # create crop
            self.create_crop_write_file(file_name)

    def create_crop_write_file(self, file_name):

        file_path = self.pos_img_dir + file_name
        self.logger.info("creating crop image: " + file_path)

        # read image
        img = cv2.imread(file_path, cv2.IMREAD_COLOR)

        # read annotation file to get annotation info
        annotation_info = self.parse_annotation_file(file_name)

        # iterate object list and create crop images
        for i, object_info in enumerate(annotation_info['object_list']):
            crop_box = object_info['bounding_box']
            cropped_img = iu.image_crop(img, crop_box[0], crop_box[1])
            out_file_name = 'c_' + os.path.splitext(file_name)[0] + '_' + str(i) + '.' + os.path.splitext(file_name)[1]
            cv2.imwrite(self.cropped_dir + out_file_name, cropped_img)

if __name__ == '__main__':

    logging.root.setLevel(level=logging.INFO)

    inria = InriaPersonDataSet()

    inria.draw_bounding_boxes_for_all()

    inria.create_crop_for_all()