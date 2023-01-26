#!/usr/bin/env python3

import os
import argparse
from io import BytesIO
from PIL import Image, ImageDraw
from flask import Flask, render_template, request, send_file, make_response


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('img_dir')
    parser.add_argument('-p', '--port', type=int, default=9000)
    return parser.parse_args()


def get_img_files(img_dir):
    return [f for f in os.listdir(img_dir) if f.endswith('.jpg')]


def build_flask_app(img_dir):
    img_files = get_img_files(img_dir)

    app = Flask(__name__, template_folder='templates',
                static_folder='static')

    @app.route('/')
    def get_root():
        # This is how you get a query param:
        # For example, in the URL http://google.com?foo=1 there is one query
        # param `foo` with value 1.
        draw_dynamic = request.args.get('dynamic') is not None

        return render_template(
            'root.html', img_dir=img_dir, num_imgs=len(img_files),
            img_files=img_files, dynamic=draw_dynamic)

    # This is how to do a path param. The string <fname> gets bound to the arg.
    @app.route('/static-img/<fname>')
    def get_img(fname):
        # Case 1: Simply send the file stored on the disk
        return send_file(os.path.join(img_dir, fname), mimetype='image/jpeg')

    @app.route('/dynamic-img/<fname>')
    def get_img_dynamic(fname):
        # Case 2: Have to render stuff onto the file
        img = Image.open(os.path.join(img_dir, fname))

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
        f.seek(0)
        return send_file(f, mimetype='image/jpeg')

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