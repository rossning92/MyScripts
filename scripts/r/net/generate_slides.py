from _shutil import *
import asyncio
from pyppeteer import launch

TITLES = '''
Function
Test
1
2
3
abc
'''.strip()

FILE_PREFIX = 'function_title'

SCALE = 1


def write_to_file(text, file_name):
    a = '''
    
    <!DOCTYPE html>
    <html>
    
    <head>
        <link href="https://fonts.googleapis.com/css?family=Arvo&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css?family=Roboto+Mono&display=swap" rel="stylesheet">
        <style>
            @import "compass/css3";
    
            @import "compass/css3/transform";
            @import url(https://fonts.googleapis.com/css?family=Bangers);
    
            body {
                background-color: #000000;
            }
    
            html,
            body {
                height: 100%;
            }
    
            html {
                display: table;
                margin: auto;
            }
    
            body {
                display: table-cell;
                vertical-align: middle;
            }
    
            h1 {
                text-align: center;
                font-weight: normal;
                color: #fff;
                /* text-transform: uppercase; */
                white-space: nowrap;
                font-size: 8vw;
                z-index: 1000;
                font-family: 'Arvo', serif;
                /*font-family: 'Roboto Mono', monospace;*/
                font-weight: bold;
                /* text-shadow: 5px 5px 0 rgba(0, 0, 0, 0.7); */
                /* @include skew(0, -6.7deg, false);
                @include transition-property(font-size);
                @include transition-duration(0.5s); */
    
            }
        </style>
    </head>
    
    <body>
    
        <h1>''' + text + '''</h1>
    
    </body>
    
    </html>
    '''

    async def main():
        browser = await launch()
        page = await browser.newPage()
        await page.setViewport({
            'width': int(1920 / SCALE),
            'height': int(1080 / SCALE),
            'deviceScaleFactor': SCALE,
        })
        # await page.goto('file://' + os.path.realpath(f).replace('\\', '/'))
        await page.goto('data:text/html,' + a)
        await page.screenshot({'path': file_name, 'omitBackground': True})
        await browser.close()

    asyncio.get_event_loop().run_until_complete(main())

if __name__ == '__main__':
    cd(r'{{WORK_DIR}}')

    for i, line in enumerate(TITLES.splitlines()):
        print(i)
        write_to_file(line, '%s_%02d.png' % (FILE_PREFIX, i + 1))
