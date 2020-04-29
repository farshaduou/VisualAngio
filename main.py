# https://github.com/lorensen/VTKExamples/blob/master/src/Python/Utilities/VTKWithNumpy.py

import numpy as np
import vtk

def load_volume(filename):
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(filename)
    reader.Update()
    (xMin, xMax, yMin, yMax, zMin, zMax) = reader.GetExecutive().GetWholeExtent(reader.GetOutputInformation(0))
    (xSpacing, ySpacing, zSpacing) = reader.GetOutput().GetSpacing()
    (x0, y0, z0) = reader.GetOutput().GetOrigin()
    center = [x0 + xSpacing * 0.5 * (xMin + xMax),
            y0 + ySpacing * 0.5 * (yMin + yMax),
            z0 + zSpacing * 0.5 * (zMin + zMax)]


    # The following class is used to store transparency-values for later retrival.
    #  In our case, we want the value 0 to be
    # completely opaque whereas the three different cubes are given different transparency-values to show how it works.
    alphaChannelFunc = vtk.vtkPiecewiseFunction()
    alphaChannelFunc.AddPoint(0, 0.0)
    alphaChannelFunc.AddPoint(50, 0.05)
    alphaChannelFunc.AddPoint(100, 0.1)
    alphaChannelFunc.AddPoint(150, 0.2)

    # This class stores color data and can create color tables from a few color points.
    #  For this demo, we want the three cubes to be of the colors red green and blue.
    colorFunc = vtk.vtkColorTransferFunction()
    colorFunc.AddRGBPoint(50, 1.0, 0.0, 0.0)
    colorFunc.AddRGBPoint(100, 0.0, 1.0, 0.0)
    colorFunc.AddRGBPoint(150, 0.0, 0.0, 1.0)

    # The previous two classes stored properties.
    #  Because we want to apply these properties to the volume we want to render,
    # we have to store them in a class that stores volume properties.
    volumeProperty = vtk.vtkVolumeProperty()
    volumeProperty.SetColor(colorFunc)
    volumeProperty.SetScalarOpacity(alphaChannelFunc)

    volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()
    volumeMapper.SetInputConnection(reader.GetOutputPort())

    # The class vtkVolume is used to pair the previously declared volume as well as the properties
    #  to be used when rendering that volume.
    volume = vtk.vtkVolume()
    volume.SetMapper(volumeMapper)
    volume.SetProperty(volumeProperty)

    return volume

def main():
    volume = load_volume('data/Normal-001/MRA/Normal001-MRA.mha')

    # Create the renderer
    renderer = vtk.vtkRenderer()
    renderWin = vtk.vtkRenderWindow()
    renderWin.AddRenderer(renderer)
    renderInteractor = vtk.vtkRenderWindowInteractor()
    renderInteractor.SetRenderWindow(renderWin)
    renderInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

    # We add the volume to the renderer
    renderer.AddVolume(volume)
    colors = vtk.vtkNamedColors()
    renderer.SetBackground(colors.GetColor3d("MistyRose"))

    # ... and set window size.
    renderWin.SetSize(900, 900)

    def vtkSliderCallback2(obj, event):
        new_slice = int(obj.GetRepresentation().GetValue())
        reslice.Update()
        sliceSpacing = reslice.GetOutput().GetSpacing()[2]
        matrix = reslice.GetResliceAxes()
        matrix.SetElement(0, 3, new_slice)

    SliderRepres = vtk.vtkSliderRepresentation2D()
    slider_min = 0
    slider_max = 200
    SliderRepres.SetMinimumValue(slider_min)
    SliderRepres.SetMaximumValue(slider_max)
    SliderRepres.SetValue((slider_min + slider_max) / 2)
    SliderRepres.SetTitleText("Slice")
    SliderRepres.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    SliderRepres.GetPoint1Coordinate().SetValue(0.2, 0.6)
    SliderRepres.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    SliderRepres.GetPoint2Coordinate().SetValue(0.4, 0.6)

    SliderRepres.SetSliderLength(0.02)
    SliderRepres.SetSliderWidth(0.03)
    SliderRepres.SetEndCapLength(0.01)
    SliderRepres.SetEndCapWidth(0.03)
    SliderRepres.SetTubeWidth(0.005)
    SliderRepres.SetLabelFormat("%3.0lf")
    SliderRepres.SetTitleHeight(0.02)
    SliderRepres.SetLabelHeight(0.02)

    SliderWidget = vtk.vtkSliderWidget()
    SliderWidget.SetInteractor(renderInteractor)
    SliderWidget.SetRepresentation(SliderRepres)
    SliderWidget.KeyPressActivationOff()
    SliderWidget.SetAnimationModeToAnimate()
    SliderWidget.SetEnabled(True)
    SliderWidget.AddObserver("InteractionEvent", vtkSliderCallback2)

    # A simple function to be called when the user decides to quit the application.
    def exitCheck(obj, event):
        if obj.GetEventPending() != 0:
            obj.SetAbortRender(1)

    # Tell the application to use the function as an exit check.
    renderWin.AddObserver("AbortCheckEvent", exitCheck)

    renderInteractor.Initialize()
    # Because nothing will be rendered without any input, we order the first render manually
    #  before control is handed over to the main-loop.
    renderWin.Render()
    renderInteractor.Start()


if __name__ == '__main__':
    main()