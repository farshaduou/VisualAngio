# VisualAngio

VisualAngio is an interactive visualization tool for better understanding of cerebrovasculature structure.
<p align="center">
  <img src = "/Final%20Report/images/preview.png" width="500px"/>
</p>

# How to Run

Install vtk in conda/virtualenv. Then run:

Run `python main.py`

Example data file provided.
For more data points you can download the dataset from [here](https://public.kitware.com/Wiki/TubeTK/Data). Extract the files, then move the folder inside and call it `data`.

```
mv "ITKTubeTK - Bullitt - Healthy MR Database/Designed Database of MR Brain Images of Healthy Volunteers/" data
```

# How the UI works:

You can navigate through the slices of MRA images using the scroller: 
<p align="center">
  <img src = "/Final%20Report/images/1.png"/>
</p>
  
Select a location in the image to track the vasculature at the surrounding region:
<p align="center">
  <img src = "/Final%20Report/images/2.png"/>
</p>

Use mouse to interact with the UI to view the vasculature structure at the region of interest from different angles to track the 3D structure better: 

<p align="center">
  <img src = "/Final%20Report/images/3.png"/>
</p>
