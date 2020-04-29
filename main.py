import numpy as np
import vtk

def load_volume(filename):
    reader = vtk.vtkMetaImageReader()
    reader.SetFileName(filename)
    reader.Update()
    (xMin, xMax, yMin, yMax, zMin, zMax) = reader.GetExecutive().GetWholeExtent(reader.GetOutputInformation(0))
    (xSpacing, ySpacing, zSpacing) = reader.GetOutput().GetSpacing()
    (x0, y0, z0) = reader.GetOutput().GetOrigin()
    print(f'Origin: {(x0, y0, z0)}')
    print(f'Extents: min: {(xMin, yMin, zMin)}')
    print(f'         max: {(xMax, yMax, zMax)}')
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

    return volume, reader.GetOutputPort()

def volume_subset(image):
    voi = vtk.vtkExtractVOI()
    voi.SetInputConnection(image)
    voi.SetVOI(0, 447, 0, 447, 0, 127)

    mapper = vtk.vtkFixedPointVolumeRayCastMapper()
    mapper.SetInputConnection(voi.GetOutputPort())
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

    volume = vtk.vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(volumeProperty)
    return voi, volume

def load_slice(image):
    im = vtk.vtkImageResliceMapper()
    im.SetInputConnection(image)
    # im.SliceFacesCameraOn()
    # im.SliceAtFocalPointOn()
    im.BorderOff()
    plane = im.GetSlicePlane()
    plane.SetNormal(1.0, 0.0, 0.0)
    plane.SetOrigin(114, 114, 50)

    ip = vtk.vtkImageProperty()
    ip.SetColorWindow(2000)
    ip.SetColorLevel(1000)
    ip.SetAmbient(0.0)
    ip.SetDiffuse(1.0)
    ip.SetOpacity(1.0)
    ip.SetInterpolationTypeToLinear()

    ia = vtk.vtkImageSlice()
    ia.SetMapper(im)
    ia.SetProperty(ip)

    return im, ia

debug_sphere = None
# To handle click events
class MouseInteractorHighLightActor(vtk.vtkInteractorStyleTrackballCamera):
 
    def __init__(self,parent=None):
        self.AddObserver("LeftButtonPressEvent",self.leftButtonPressEvent)
        self.subset = None
    
    def set_voi(self, voi):
        self.voi = voi
 
    def leftButtonPressEvent(self,obj,event):
        global debug_sphere
        self.OnLeftButtonDown()
        clickPos = self.GetInteractor().GetEventPosition()

        picker = vtk.vtkCellPicker()
        picker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())
        world_pos = [int(x) for x in picker.GetPickPosition()]
        maxes = [447, 447, 127]
        if any((world_pos[i] < 0 or world_pos[i] > maxes[i]) for i in range(3)):
            self.OnLeftButtonDown()
            return

        print(world_pos)
        world_pos = (114, 114, 50)
        debug_sphere.SetCenter(*world_pos)

        d = 35 # Size of box
        voi_min = [max(x - d, 0) for x in world_pos]
        voi_max = [min(world_pos[i] + d, maxes[i]) for i in range(3)]
        print(voi_min, voi_max)
        self.voi.SetVOI(
            voi_min[0], voi_max[0],
            voi_min[1], voi_max[1],
            voi_min[2], voi_max[2],
        )
        
        # self.OnLeftButtonDown()


def main():
    global debug_sphere
    # volume is the VTK object we render. image is loaded from the file
    _, image = load_volume('data/Normal-001/MRA/Normal001-MRA.mha')

    # load the slice
    slice_im, slice_ia = load_slice(image)

    # Subset
    voi, subset_actor = volume_subset(image)

    # Create the renderer
    renderer = vtk.vtkRenderer()
    renderWin = vtk.vtkRenderWindow()
    renderWin.AddRenderer(renderer)
    renderInteractor = vtk.vtkRenderWindowInteractor()
    renderInteractor.SetRenderWindow(renderWin)
    style = MouseInteractorHighLightActor()
    style.SetDefaultRenderer(renderer)
    style.set_voi(voi)
    renderInteractor.SetInteractorStyle(style)
    # renderInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
    colors = vtk.vtkNamedColors()
    renderer.SetBackground(colors.GetColor3d("black"))

    # Setup camera
    camera = vtk.vtkCamera()
    camera.SetPosition(-400, 114, 50)
    camera.SetFocalPoint(114, 114, 50)
    camera.SetViewUp(0, 0.0, 1.0)
    renderer.SetActiveCamera(camera)


    # Add stuff
    renderer.AddActor(slice_ia)
    renderer.AddActor(subset_actor)
    # renderer.AddVolume(volume)

    # ... and set window size.
    renderWin.SetSize(900, 900)

    ##### DEBUG SPHERE
    debug_sphere = vtk.vtkSphereSource()
    debug_sphere.SetCenter(0,0,0)
    debug_sphere.SetRadius(5.0)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(debug_sphere.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # assign actor to the renderer
    renderer.AddActor(actor)
    ############

    def vtkSliderCallback2(obj, event):
        new_slice = int(obj.GetRepresentation().GetValue())
        plane = slice_im.GetSlicePlane()
        plane.SetOrigin(new_slice, 114, 50)

    slider = vtk.vtkSliderRepresentation2D()
    slider.SetMinimumValue(0)
    slider.SetMaximumValue(240)
    slider.SetValue(144)
    slider.SetTitleText("Slice")
    slider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slider.GetPoint1Coordinate().SetValue(0.7, 0.9)
    slider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slider.GetPoint2Coordinate().SetValue(0.9, 0.9)

    slider.SetSliderLength(0.02)
    slider.SetSliderWidth(0.03)
    slider.SetEndCapLength(0.01)
    slider.SetEndCapWidth(0.03)
    slider.SetTubeWidth(0.005)
    slider.SetLabelFormat("%3.0lf")
    slider.SetTitleHeight(0.02)
    slider.SetLabelHeight(0.02)

    slider_widget = vtk.vtkSliderWidget()
    slider_widget.SetInteractor(renderInteractor)
    slider_widget.SetRepresentation(slider)
    slider_widget.KeyPressActivationOff()
    slider_widget.SetAnimationModeToAnimate()
    slider_widget.SetEnabled(True)
    slider_widget.AddObserver("InteractionEvent", vtkSliderCallback2)

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