from os.path import isfile
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import datetime
import email.utils
import mimetypes
import posixpath
import shutil
from http import HTTPStatus
import json
import logging
import sys
import argparse

from fib_game import *

PORT = 8080
SERVER_ADDRESS = '127.0.0.1'
SITE_FOLDER = 'site'
SITE_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), SITE_FOLDER)

PATH_ALIASES = {'/': 'host.html'}

# global game instance
FIB_GAME = FibGame(r"D:\dev\fibbage-online\content\Fibbage XL (steam)\content")

POST_RETURN_CODE = "return_code"
POST_LOCATION = "location"
POST_ERROR_MESSAGE = "error_message"
POST_DATA = "data"

# based on http.server.SimpleHTTPRequestHandler
class HorribleHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "HorribleHTTP/0.1"


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            try:
                shutil.copyfileobj(f, self.wfile)
            finally:
                f.close()


    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()
        if f:
            f.close()


    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        json_data = json.loads(post_data.decode('utf-8'))

        logging.debug("POST for %s: %s" % (self.path, json_data))

        return_code, data = FIB_GAME.handle_POST(self.path, json_data)
        logging.debug("POST handler returned %s and %s" % (RETURN_CODES_TO_NAMES[return_code], data))

        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        reply_json = {POST_RETURN_CODE: return_code}

        if return_code in (POST_INTERNAL_ERROR, POST_VALIDATION_ERROR, POST_ENDPOINT_NOT_FOUND):
            reply_json[POST_ERROR_MESSAGE] = data
        elif return_code == POST_REDIRECT:
            if not data.startswith('/'):
                data = '/' + data
            reply_json[POST_LOCATION] = data
        elif return_code == POST_REPLY:
            reply_json[POST_DATA] = data
        else:
            raise Exception("Unexpected return code %d from POST handler" % return_code)

        self.wfile.write(json.dumps(reply_json).encode('utf-8'))


    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.
        """
        page_path = self.path

        # ignore everything after # in GET/HEAD requests
        if '#' in page_path:
            page_path = page_path[:page_path.index('#')]

        # self.path is what comes after the host (the first / and everything that comes after it)
        if page_path in PATH_ALIASES:
            page_path = PATH_ALIASES[page_path]

        # convert slashes, remove leading shash
        page_path = page_path.replace('/', os.path.sep).lstrip(os.path.sep)
        
        allow_caching = True

        # make sure this isn't a round-specific GET request
        game_supplied_path = FIB_GAME.handle_GET(page_path)
        if game_supplied_path is not None:
            page_path = game_supplied_path
            # ask browser to never cache these, as the content changes
            # but the URL remains the same
            allow_caching = False
        else:
            # try to resolve into the site folder
            page_path = os.path.abspath(os.path.join(SITE_FOLDER_PATH, page_path))

            # test for folder traversal attempts
            if not page_path.startswith(SITE_FOLDER_PATH):
                logging.ERROR("URL path %s not resolved" % self.path)
                self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                return None

            # if a GET request path has no extension - try
            # to resolve it by appending .html
            if (not os.path.isfile(page_path) and
                    len(os.path.splitext(page_path)[1]) == 0 and 
                    os.path.isfile(page_path + '.html')):
                page_path += '.html'

        try:
            f = open(page_path, 'rb')
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())

            # Use browser cache if possible
            if ("If-Modified-Since" in self.headers
                    and "If-None-Match" not in self.headers
                    and allow_caching):
                # compare If-Modified-Since and time of last file modification
                try:
                    ims = email.utils.parsedate_to_datetime(
                        self.headers["If-Modified-Since"])
                except (TypeError, IndexError, OverflowError, ValueError):
                    # ignore ill-formed values
                    pass
                else:
                    if ims.tzinfo is None:
                        # obsolete format with no timezone, cf.
                        # https://tools.ietf.org/html/rfc7231#section-7.1.1.1
                        ims = ims.replace(tzinfo=datetime.timezone.utc)
                    if ims.tzinfo is datetime.timezone.utc:
                        # compare to UTC datetime of last modification
                        last_modif = datetime.datetime.fromtimestamp(
                            fs.st_mtime, datetime.timezone.utc)
                        # remove microseconds, like in If-Modified-Since
                        last_modif = last_modif.replace(microsecond=0)

                        if last_modif <= ims:
                            self.send_response(HTTPStatus.NOT_MODIFIED)
                            self.end_headers()
                            f.close()
                            return None

            content_type = self.guess_type(page_path)

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", content_type) # restricted to only
            self.send_header("Content-Length", str(fs[6]))
            if allow_caching:
                self.send_header("Last-Modified",
                    self.date_time_string(fs.st_mtime))
            self.end_headers()
            return f
        except:
            f.close()
            raise


    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """

        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logs', action='store_true', help='display more logs')
    args = parser.parse_args()

    root = logging.getLogger()
    if args.logs:
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.WARNING)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s, %(name)s [%(levelname)s]: %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

    with HTTPServer((SERVER_ADDRESS, PORT), HorribleHTTPRequestHandler) as httpd:
        print("serving at port", PORT)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Bye")
            return

if "__main__" == __name__:
    main()