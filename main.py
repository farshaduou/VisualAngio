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


    alphaChannelFunc = vtk.vtkPiecewiseFunction()
    alphaChannelFunc.AddPoint(0, 0.0)
    alphaChannelFunc.AddPoint(130, 0.01)
    alphaChannelFunc.AddPoint(400, 0.27)
    alphaChannelFunc.AddPoint(650, 0.9)
    alphaChannelFunc.AddPoint(1106, 1.0)


    colorFunc = vtk.vtkColorTransferFunction()
    colorFunc.AddRGBPoint(0, 0.0, 0.0, 0.0)
    colorFunc.AddRGBPoint(400, 1.0, 0.0, 0.0)
    colorFunc.AddRGBPoint(650, 1.0, 0.0, 0.0)
    colorFunc.AddRGBPoint(230, 1.0, 0.0, 0.0)
    colorFunc.AddRGBPoint(1106, 0.0, 0.0, 1.0)

    # The previous two classes stored properties.
    #  Because we want to apply these properties to the volume we want to render,
    # we have to store them in a class that stores volume properties.
    volumeProperty = vtk.vtkVolumeProperty()
    volumeProperty.SetColor(colorFunc)
    volumeProperty.SetScalarOpacity(alphaChannelFunc)

    volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()
    volumeMapper.CroppingOn()
    volumeMapper.SetInputConnection(reader.GetOutputPort())

    # The class vtkVolume is used to pair the previously declared volume as well as the properties
    #  to be used when rendering that volume.
    volume = vtk.vtkVolume()
    volume.SetMapper(volumeMapper)
    volume.SetProperty(volumeProperty)
    volume.SetPickable(False)

    return volume, reader.GetOutputPort()

def load_isosurface(image):
    iso = vtk.vtkContourFilter()
    # iso = vtk.vtkMarchingCubes()
    iso.SetInputConnection(image)
    iso.ComputeNormalsOn()
    for i in range(8):
        iso.SetValue(i, i*33.33 + 266.67)
    iso.Update()

    isoMapper = vtk.vtkPolyDataMapper()
    isoMapper.SetInputData(iso.GetOutput())
    isoMapper.ScalarVisibilityOff()

    # Take the isosurface data and create geometry
    actor = vtk.vtkLODActor()
    actor.SetNumberOfCloudPoints( 1000000 )
    actor.SetMapper(isoMapper)
    actor.SetVisibility(False)
    actor.GetProperty().SetColor( 1, 0, 0 )
    return actor

def load_slice(image):
    im = vtk.vtkImageResliceMapper()
    im.SetInputConnection(image)
    im.BorderOff()
    plane = im.GetSlicePlane()
    plane.SetNormal(1.0, 0.0, 0.0)
    plane.SetOrigin(114, 114, 50)

    ip = vtk.vtkImageProperty()
    ip.SetColorWindow(2000)
    ip.SetColorLevel(500)
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
        self.AddObserver("KeyPressEvent",self.keyPressEvent)
        self.subset = None
        self.world_pos = [0, 0, 0]
    
    def set_voi(self, voi):
        self.voi = voi
    
    def set_isosurface(self, iso_actor):
        self.iso_actor = iso_actor

    def update_crop(self, world_pos):
        maxes = [447, 447, 127]
        if any((world_pos[i] < 0 or world_pos[i] > maxes[i]) for i in range(3)):
            return
        world_pos = [int(x) for x in world_pos]
        self.world_pos = world_pos
        maxes = [447, 447, 127]

        # print(f'world_pos: {world_pos}')
        debug_sphere.SetCenter(*world_pos)
        debug_sphere.SetRadius(1.1)

        d = 25 # Size of box
        voi_min = [max(x - d, 0) for x in world_pos]
        voi_max = [min(world_pos[i] + d, maxes[i]) for i in range(3)]
        self.voi.SetCroppingRegionPlanes(
            voi_min[0], voi_max[0],
            voi_min[1], voi_max[1],
            voi_min[2], voi_max[2],
        )
        self.voi.Update()

    def update_params(self,world_pos):
        self.voi.SetProperty(volumeProperty)

    def keyPressEvent(self,obj,event):
        key = self.GetInteractor().GetKeySym()
        if key == 'space':
            vis = self.iso_actor.GetVisibility()
            self.iso_actor.SetVisibility(not vis)
            self.GetInteractor().Render()
 
    def leftButtonPressEvent(self,obj,event):
        global debug_sphere
        self.OnLeftButtonDown()
        clickPos = self.GetInteractor().GetEventPosition()

        picker = vtk.vtkCellPicker()
        picker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())
        world_pos = picker.GetPickPosition()
        self.update_crop(world_pos)

        self.OnLeftButtonDown()

def main():
    global debug_sphere
    # volume is the VTK object we render. image is loaded from the file
    volume, image = load_volume('data/Normal-001/MRA/Normal001-MRA.mha')

    # load the slice
    slice_im, slice_ia = load_slice(image)

    # load isosurface
    iso_actor = load_isosurface(image)

    # Create the renderer
    renderer = vtk.vtkRenderer()
    renderWin = vtk.vtkRenderWindow()
    renderWin.AddRenderer(renderer)
    renderInteractor = vtk.vtkRenderWindowInteractor()
    renderInteractor.SetRenderWindow(renderWin)
    mouse_interactor = MouseInteractorHighLightActor()
    mouse_interactor.SetDefaultRenderer(renderer)
    mouse_interactor.set_voi(volume.GetMapper())
    mouse_interactor.set_isosurface(iso_actor)
    renderInteractor.SetInteractorStyle(mouse_interactor)
    # renderInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
    colors = vtk.vtkNamedColors()
    renderer.SetBackground(colors.GetColor3d("#505050"))

    # Setup camera
    camera = vtk.vtkCamera()
    camera.SetPosition(-400, 114, 50)
    camera.SetFocalPoint(114, 114, 50)
    camera.SetViewUp(0, 0.0, 1.0)
    renderer.SetActiveCamera(camera)

    # Add stuff
    renderer.AddActor(slice_ia)
    renderer.AddActor(iso_actor)
    renderer.AddVolume(volume)

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

        world_pos = mouse_interactor.world_pos
        world_pos = (new_slice, *world_pos[1:])
        mouse_interactor.update_crop(world_pos)

    def vtkOpacitySliderCallback(obj,event):
        #current_slice = int(obj.GetRepresentation().GetValue())
        #world_pos = mouse_interactor.world_pos
        #world_pos = (current_slice, *world_pos[1:])
        world_pos = mouse_interactor.world_pos
        mouse_interactor.update_params(world_pos)


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

    """
    # Opacity Slider
    slider2 = vtk.vtkSliderRepresentation2D()
    slider2.SetMinimumValue(0)
    slider2.SetMaximumValue(0.5)
    slider2.SetValue(0.05)
    slider2.SetTitleText("Opacity")
    slider2.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slider2.GetPoint1Coordinate().SetValue(0.7, 0.8)
    slider2.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slider2.GetPoint2Coordinate().SetValue(0.9, 0.8)

    slider2.SetSliderLength(0.02)
    slider2.SetSliderWidth(0.03)
    slider2.SetEndCapLength(0.01)
    slider2.SetEndCapWidth(0.03)
    slider2.SetTubeWidth(0.005)
    slider2.SetLabelFormat("%3.0lf")
    slider2.SetTitleHeight(0.02)
    slider2.SetLabelHeight(0.02)
    
    slider_widget2 = vtk.vtkSliderWidget()
    slider_widget2.SetInteractor(renderInteractor)
    slider_widget2.SetRepresentation(slider2)
    slider_widget2.KeyPressActivationOff()
    slider_widget2.SetAnimationModeToAnimate()
    slider_widget2.SetEnabled(True)
    slider_widget2.AddObserver("InteractionEvent", vtkOpacitySliderCallback)
    """
    # widget
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