from cgi import parse_qs
from PIL import Image, ImageDraw, ImageFont
import cups

NUMBER_KEY = 'number'
TIME_KEY = 'time'
SHOW_KEY = 'show'
BACKDROP_IMAGE = 'backdrop.png'
FONT_FILE = 'FreeSerifBold.ttf'

def application(environ, start_response):
    '''
    Serves an incoming request.
    
    @type environ C{dict}
    @param environ a request environment
    @type start_response C{function}
    @param start_response a response function
    @rtype C{list}
    @return content pieces
    '''

    # Check request path.
    path_string = environ.get('PATH_INFO', '/')
    path = filter(lambda x: len(x) > 0, path_string.split('/'))
    if len(path) != 1 or path[0] != 'ticket':
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return ['404 Not Found']

    # Parse parameters.
    number = None
    time = None
    parameters = parse_qs(environ.get('QUERY_STRING', ''))
    if NUMBER_KEY in parameters and parameters[NUMBER_KEY][0].isdigit():
        number = str(int(parameters[NUMBER_KEY][0]))
    if TIME_KEY in parameters: 
        time_parts = parameters[TIME_KEY][0].split(':')
        while len(time_parts) < 2:
            time_parts.append(0)
        if (isinstance(time_parts[0], int) or time_parts[0].isdigit())\
            and (isinstance(time_parts[1], int) or time_parts[1].isdigit()):
            time = '%02d:%02d' % (int(time_parts[0]), int(time_parts[1]))
    if number is None or time is None:
        start_response('422 Unprocessable Entity', [('Content-Type', 'text/plain')])
        return ['422 Unprocessable Entity']

    # Create ticket image.
    filename = 'tmp/ticket%s.png' % (number)
    write_image(number, time, filename)        

    # Image show test.
    if SHOW_KEY in parameters:
        return serve_file(environ, start_response, filename, 'image/png')
    
    # Print using CUPS.
    con = cups.Connection()
    con.printFile(con.getDefault(), filename, 'Ticket Request', {})
    
    # Acknowledge with response.
    start_response('200 Ok', [('Content-Type', 'text/plain')])
    return ['Ticket printed']


def write_image(number, time, filename):
    '''
    Writes an image of the ticket.
    
    @type number C{int}
    @param number a ticket number
    @type time C{str}
    @param time a ticket time
    @type filename C{str}
    @param filename a file to write
    '''
    
    # Copy the backdrop image.
    image = Image.open(BACKDROP_IMAGE).copy()
    draw = ImageDraw.Draw(image)
    
    # Write number
    font = ImageFont.truetype(FONT_FILE, 80)
    (w,h) = draw.textsize(number, font)
    draw.text((int(84-w/2),int(120-h/2)), number, (0,0,0), font)
    
    # Write time.
    font = ImageFont.truetype(FONT_FILE, 32)
    (w,h) = draw.textsize(time, font)
    draw.text((int(84-w/2),int(250-h/2)), time, (0,0,0), font)
    
    image.save(filename)


def serve_file(environ, start_response, filename, content_type):
    '''
    Serves a file from disk to response.
    
    @type environ C{dict}
    @param environ a request environment
    @type start_response C{function}
    @param start_response a response function
    @type filename C{str}
    @param filename a file to serve
    @type content_type C{str}
    @param content_type a file content type
   '''
    f = open(filename)
    start_response('200 Ok', [('Content-Type', content_type)])
    if 'wsgi.file_wrapper' in environ:
        return environ['wsgi.file_wrapper'](f, 1024)
    else:
        return iter(lambda: f.read(1024), '')
