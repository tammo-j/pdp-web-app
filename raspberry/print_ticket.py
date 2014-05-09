import cgi
import cups
from PIL import Image, ImageDraw, ImageFont
from settings import CLIENT_PRINTER, ADMIN_PRINTER
from datetime import datetime

NUMBER_KEY = 'number'
TIME_KEY = 'time'
SHOW_KEY = 'show'
BACKDROP_IMAGE = 'backdrop.png'
MID_X = 84
NUM_Y = 120
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
    if len(path) != 1 or (path[0] != 'ticket' and path[0] != 'ticketadmin'):
        start_response('404 Not Found', [
                ('Access-Control-Allow-Origin','*'),
                ('Content-Type', 'text/plain')])
        return ['404 Not Found']
    
    # Determine which ticket is printed.
    admin_ticket = (path[0] == 'ticketadmin')

    # Get parameters.
    post = cgi.FieldStorage(
        fp=environ['wsgi.input'],
        environ=environ
    )

    # Parse parameters.
    number = None
    time = None
    if 'number' in post and 'time' in post and post['number'].value.isdigit():
        number = str(post['number'].value)
        time = str(post['time'].value)

    # Check everything is received.
    if number is None or time is None:
        start_response('422 Unprocessable Entity', [
                ('Access-Control-Allow-Origin','*'),
                ('Content-Type', 'text/plain')])
        return ['422 Unprocessable Entity']

    # Create ticket image.
    filename = None
    if admin_ticket:
        filename = 'tmp/adminticket%s.png' % (number)
        items = None
        price = None
        if 'items' in post and post['items'].value.isdigit():
            items = str(post['items'].value)
        if 'price' in post:
            price = str(post['price'].value)
        write_admin_image(number, time, items, price, filename)
    else:
        filename = 'tmp/ticket%s.png' % (number)
        write_image(number, time, filename)

    # Image show test.
    if 'show' in post and str(post['show'].value) == '1':
        return serve_file(environ, start_response, filename, 'image/png')
    
    # Print using CUPS.
    printer_name = None
    if admin_ticket:
        printer_name = ADMIN_PRINTER
    else:
        printer_name = CLIENT_PRINTER
    con = cups.Connection()
    printers = con.getPrinters()
    if not printer_name or printer_name not in printers:
        start_response('500 Internal Error', [
            ('Access-Control-Allow-Origin','*'),
            ('Content-Type', 'text/plain')])
        return ['500 Internal Error: Printer not found. Check the settings.py']
    con.printFile(printer_name, filename, 'Ticket Request', {})
    
    # Report success.
    start_response('200 Ok', [
                ('Access-Control-Allow-Origin','*'),
                ('Content-Type', 'text/plain')])
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
    
    # Write texts.
    add_text(draw, MID_X, 29, 18, 'Ticket Number:')
    add_text(draw, MID_X, NUM_Y, 80, number)
    add_text(draw, MID_X, 213, 18, 'Ready at:')
    add_text(draw, MID_X, 250, 32, time)
        
    image.save(filename)


def write_admin_image(number, time, items, price, filename):
    '''
    Writes an image of the ticket.
    
    @type number C{int}
    @param number a ticket number
    @type time C{str}
    @param time a ticket time
    @type items C{str}
    @param items a number of items
    @type price C{str}
    @param price a total price of order
    @type filename C{str}
    @param filename a file to write
    '''
    
    # Copy the backdrop image.
    image = Image.open(BACKDROP_IMAGE).copy()
    draw = ImageDraw.Draw(image)
    
    # Write texts.
    add_text(draw, MID_X, 29, 18, 'Ticket Number:')
    add_text(draw, MID_X, NUM_Y, 80, number)
    add_text(draw, MID_X, 213, 18, 'Ready since:')
    #add_text(draw, MID_X, 250, 32, time)
    add_text(draw, MID_X, 240, 32, datetime.now().strftime('%H:%M'))
    if items is not None:
        add_text(draw, MID_X, 263, 18, '%s items' % (items))
    if price is not None:
        add_text(draw, MID_X, 280, 18, 'Price %s EUR' % (price))
    image.save(filename)


def add_text(draw, x, y, size, text, centered=True):
    '''
    Writes text using ImageDraw.
    
    @type draw C{ImageDraw}
    @param draw ImageDraw on the image to write to
    @type x C{int}
    @param x a text center x coordinate
    @type y C{int}
    @param y a text center y coordinate
    @type size C{int}
    @param size a font size
    @type text C{str}
    @param text a text to write
    @type centered C{bool}
    @param centered a flag to center the text
    '''
    font = ImageFont.truetype(FONT_FILE, size);
    (w,h) = draw.textsize(text, font)
    if centered:
        draw.text((int(x-w/2),int(y-h/2)), text, (0,0,0), font);
    else:    
        draw.text((x,int(y-h/2)), text, (0,0,0), font);


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
    start_response('200 Ok', [
                ('Access-Control-Allow-Origin','*'),
                ('Content-Type', content_type)])
    if 'wsgi.file_wrapper' in environ:
        return environ['wsgi.file_wrapper'](f, 1024)
    else:
        return iter(lambda: f.read(1024), '')


# Running this file starts the wsgiref server for testing.
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    print 'Running web service at http://localhost:8080'
    server = make_server('localhost', 8080, application)
    server.serve_forever()
