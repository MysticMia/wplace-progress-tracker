Program with some utilities for wplace. Downloads chunks from the canvas,
crops them to the right size, and compares it to a template. This yields an
image of the remaining pixels. In combination with `count_pixels.py` and
`pixel_progress_grapher.py`, a graph can be created to track the progress of
pixel placement and the number of pixels left to be placed.

## Usage
Copy the `configs/example.json` file and rename it to whatever. For example,
`configs/mia.json`. Open the file and update the top left coordinate and
image size of the template. Change the name of the directory to something
fitting, like "mia art 1".

Run the program once to create the necessary directories. It will give an
error that you're missing a template.png file.

```batch
python main.py mia
```

Here, the argument you pass is the name of the config file.

Copy your template.png file into the created directory, for example:
`/mia art 1/pictures/template.png`.

Now, run the program again.
```batch
python main.py mia
```
