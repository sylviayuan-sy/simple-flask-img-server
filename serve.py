#!/usr/bin/env python3

import os
import glob
import math
import argparse
from io import BytesIO
from PIL import Image, ImageDraw
from flask import Flask, render_template, request, send_file, make_response


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('img_dir')
    parser.add_argument('-p', '--port', type=int, default=9000)
    return parser.parse_args()

def get_sub_folders(dir):
    subdirs = os.listdir(dir)
    subdir_images = {}
    for subdir in subdirs:
        if '.jpg' in subdir or '.png' in subdir:
            if 'main' not in subdir_images.keys():
                subdir_images['main'] = []
            subdir_images['main'].append(subdir)
        else: 
            images = os.listdir(os.path.join(dir, subdir))
            subdir_images[subdir] = [f for f in images if f.endswith('.jpg') or f.endswith('.png')]
            subdir_images[subdir].sort()
    subdir_images["main"].sort()
    return subdir_images

# def get_img_files(img_dir):
#     return [f for f in os.listdir(img_dir) if f.endswith('.jpg')]


def build_flask_app(img_dir):
    img_files_dict = get_sub_folders(img_dir)
    keys = list(img_files_dict.keys())

    global split_img_files_dict 
    split_img_files_dict = {}

    IMAGE_CAP = 10

    for key in keys:
        if len(img_files_dict[key]) > IMAGE_CAP:
            for i in range(math.ceil(len(img_files_dict[key])/IMAGE_CAP)):
                split_img_files_dict[f'{key} page {i+1}'] = img_files_dict[key][i * IMAGE_CAP: (i+1) * IMAGE_CAP]
        else:
            split_img_files_dict[f'{key} page 1'] = img_files_dict[key]

    keys = list(split_img_files_dict)

    global all_entries_dict
    all_entries_dict = {}
    for key in keys:
        all_entries_dict[key] = len(img_files_dict[key.split(" page ")[0]])

    # breakpoint()

    app = Flask(__name__, template_folder='templates',
                static_folder='static')

    global curr_page
    curr_page = 1

    global subdir
    subdir = img_dir

    @app.route('/')
    def get_root():
        # This is how you get a query param:
        # For example, in the URL http://google.com?foo=1 there is one query
        # param `foo` with value 1.
        global all_entries_dict
        draw_dynamic = request.args.get('dynamic') is not None
        all_main = all_entries_dict["main page 1"]
        return render_template(
            'root.html', img_dir=img_dir, num_imgs=f'Showing {min(all_main, IMAGE_CAP)} out of {all_main}',
            img_files=split_img_files_dict['main page 1'], dynamic=draw_dynamic)

    @app.route("/", methods=['POST'])
    def index():
        global curr_page
        if request.method == 'POST':
            if request.form.get('action1') == 'Previous':
                if curr_page > 1:
                    curr_page -= 1
                return displayitems(curr_page)
            elif  request.form.get('action2') == 'Next':
                if curr_page < len(keys):
                    curr_page += 1
                return displayitems(curr_page)
            else:
                pass # unknown

    @app.route('/displayitems/<page>/')
    def displayitems(page=1):
        global subdir
        global all_entries_dict
        draw_dynamic = request.args.get('dynamic') is not None
        global split_img_files_dict
        items_per_page = IMAGE_CAP
        if "main" not in keys[page-1]:
            subdir = os.path.join(img_dir, keys[page-1].split(" page ")[0])
        else:
            subdir = img_dir
        print(page, subdir, keys[page-1], split_img_files_dict[keys[page-1]])
        num_entries = len(split_img_files_dict[keys[page-1]])
        num_all = all_entries_dict[keys[page-1]]
        return render_template(
                    'root.html', img_dir=subdir, num_imgs=f'Showing {min(num_entries, IMAGE_CAP)} out of {num_all}',
                    img_files=split_img_files_dict[keys[page-1]], dynamic=draw_dynamic)

    # This is how to do a path param. The string <fname> gets bound to the arg.
    @app.route('/static-img/<fname>')
    def get_img(fname):
        global subdir
        # Case 1: Simply send the file stored on the disk
        return send_file(os.path.join(subdir, fname), mimetype='image/jpeg')

    @app.route('/dynamic-img/<fname>')
    def get_img_dynamic(fname):
        global subdir
        # Case 2: Have to render stuff onto the file
        img = Image.open(os.path.join(subdir, fname))
        # print(os.path.join(img_dir, fname))

        # Do manipulations. Basically, do whatever you want, but you need
        # to turn it back into a PIL image object by the end.

        # Toy example: bbox 10% of the way into the image as an example
        width, height = img.size
        x1 = int(width * 0.1)
        y1 = int(height * 0.1)
        x2 = int(width * 0.9)
        y2 = int(height * 0.9)
        draw = ImageDraw.Draw(img)
        draw.rectangle((x1, y1, x2, y2), outline='red', width=5)

        # Have to make a "fake file"
        f = BytesIO()
        img.save(fp=f, format='jpeg')
        resp = make_response(f.getvalue())
        resp.headers['Content-type'] = 'image/jpeg'
        return resp

    return app

def main(img_dir, port):
    # NOTES:
    # This is a basic flask webserver
    # 1. List all of the files in img_dir
    # 2. Serve static webpage of the files in img_dir
    app = build_flask_app(img_dir)

    # Serve updated templates if they are edited when the server is running
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # debug=true means the server will restart when the code is edited
    app.run(debug=True, port=port, host='0.0.0.0')


if __name__ == '__main__':
    main(**vars(get_args()))