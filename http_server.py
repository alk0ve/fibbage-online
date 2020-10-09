from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import datetime
import email.utils
import mimetypes
import posixpath
import shutil
from http import HTTPStatus
import json

PORT = 8080
SERVER_ADDRESS = '127.0.0.1'
SITE_FOLDER = 'site'
SITE_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), SITE_FOLDER)

PATH_ALIASES = {'/': 'host.html', '/host':'host.html', '/':'play.html', '/question':'/question.html', '/data':'/data.jet'}
ALLOWED_EXTENSIONS = ['.html', '.htm', '.js', 'jet']


# based on http.server.SimpleHTTPRequestHandler
class HorribleHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "HorribleHTTP/0.1"


    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = os.getcwd()
        self.directory = directory
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


    def _set_response(self):
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'text/html')
        self.end_headers()


    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        json_data = json.loads(post_data.decode('utf-8'))
        print("POST for %s: %s" % (self.path, json_data))

        self._set_response()
        # send reply JSON
        reply = {"reply": "ok"}
        self.wfile.write(json.dumps(reply).encode('utf-8'))


    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.
        """

        # self.path is what comes after the host (the first / and everything that comes after it)
        page_path = self.path
        if page_path in PATH_ALIASES:
            page_path = PATH_ALIASES[page_path]

        # convert slashes, remove leading shash
        page_path = page_path.replace('/', os.path.sep).lstrip(os.path.sep)
        
        page_path = os.path.abspath(os.path.join(SITE_FOLDER_PATH, page_path))

        if not page_path.startswith(SITE_FOLDER_PATH):
            print("URL path %s not resolved" % self.path)
            breakpoint()
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        try:
            f = open(page_path, 'rb')
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())
            # Use browser cache if possible
            if ("If-Modified-Since" in self.headers
                    and "If-None-Match" not in self.headers):
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

            ctype = self.guess_type(page_path)

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype) # restricted to only
            self.send_header("Content-Length", str(fs[6]))
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



with HTTPServer((SERVER_ADDRESS, PORT), HorribleHTTPRequestHandler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()

