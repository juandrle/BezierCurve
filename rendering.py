import glfw
import imgui
import numpy as np
import moderngl as mgl
import os

from imgui.integrations.glfw import GlfwRenderer


class Scene:
    """
        OpenGL 2D scene class
    """
    # initialization
    def __init__(self,
                width,
                height,
                bezier_curve_callback,
                scene_title         = "2D Scene",
                interpolation_fct   = None):

        self.width              = width
        self.height             = height
        self.scene_title        = scene_title
        self.points             = []
        self.points_on_bezier_curve = []
        self.bezier_curve_callback = bezier_curve_callback
        self.curve_type         = 'orthographic'
        self.show_spline        = True

        # Rendering
        self.ctx                = None              # Assigned when calling init_gl()
        self.bg_color           = (0.1, 0.1, 0.1)
        self.point_size         = 7
        self.point_color        = (1.0, 0.5, 0.5)
        self.line_color         = (0.5, 0.5, 1.0)
        self.curve_color        = (1.0, 0.0, 0.0)
        self.order              = 3
        self.curve_points       = 20


    def init_gl(self, ctx):
        self.ctx        = ctx

        # Create Shaders
        self.shader = ctx.program(
            vertex_shader = """
                #version 330

                uniform mat4    m_proj;
                uniform int     m_point_size;
                uniform vec3    color;

                in vec2 v_pos;

                out vec3 f_col;

                void main() {
                    gl_Position     = m_proj * vec4(v_pos, 0.0, 1.0);
                    gl_PointSize    = m_point_size;
                    f_col           = color;
                }
            """,
            fragment_shader = """
                #version 330

                in vec3 f_col;

                out vec4 color;

                void main() {
                    color = vec4(f_col, 1.0);
                }
            """
        )
        self.shader['m_point_size'] = self.point_size

        # Set projection matrix
        l, r = 0, self.width
        b, t = self.height, 0
        n, f = -2, 2
        m_proj = np.array([
            [2/(r-l),   0,          0,          -(l+r)/(r-l)],
            [0,         2/(t-b),    0,          -(b+t)/(t-b)],
            [0,         0,          -2/(f-n),    -(n+f)/(f-n)],
            [0,         0,          0,          1]
        ], dtype=np.float32)
        m_proj = np.ascontiguousarray(m_proj.T)
        self.shader['m_proj'].write(m_proj)
        self.shader['color'] = self.point_color


    def resize(self, width, height):
        self.width  = width
        self.height = height

        # Set projection matrix
        l, r = 0, self.width
        b, t = self.height, 0
        n, f = -2, 2
        m_proj = np.array([
            [2/(r-l),   0,          0,          -(l+r)/(r-l)],
            [0,         2/(t-b),    0,          -(b+t)/(t-b)],
            [0,         0,          -2/(f-n),    -(n+f)/(f-n)],
            [0,         0,          0,          1]
        ], dtype=np.float32)
        m_proj = np.ascontiguousarray(m_proj.T)
        self.shader['m_proj'].write(m_proj)

    def knotVector_calc(self):
        part1 = [0] * self.order
        part2 = [value for value in range(1, len(self.points) - (self.order - 1))]
        part3 = [len(self.points) - (self.order - 1) for x in range(self.order)]
        return (part1 + part2 + part3)
    # set polygon
    def add_point(self, point):
        self.points.append(point)
        if len(self.points) >= self.order:
            self.points_on_bezier_curve = self.bezier_curve_callback(self.order, self.points, self.knotVector_calc(), self.curve_points)


    # clear polygon
    def clear(self):
        self.points = []
        self.points_on_bezier_curve = []


    def render(self):

        # Fill Background
        self.ctx.clear(*self.bg_color)

        # Render all points and connecting lines
        if len(self.points) > 0:
            vbo_polygon = self.ctx.buffer(np.array(self.points, np.float32))
            vao_polygon = self.ctx.vertex_array(self.shader, [(vbo_polygon, '2f', 'v_pos')])
            self.shader['color'] = self.line_color
            vao_polygon.render(mgl.LINE_STRIP)
            self.shader['color'] = self.point_color
            vao_polygon.render(mgl.POINTS)

        if self.show_spline and len(self.points_on_bezier_curve) > 1:
            self.shader['color'] = self.curve_color
            vbo_polygon = self.ctx.buffer(np.array(self.points_on_bezier_curve, np.float32))
            vao_polygon = self.ctx.vertex_array(self.shader, [(vbo_polygon, '2f', 'v_pos')])
            self.shader['color'] = self.curve_color
            vao_polygon.render(mgl.LINE_STRIP)
            self.shader['color'] = self.point_color
            vao_polygon.render(mgl.POINTS)




class RenderWindow:
    """
        GLFW Rendering window class
        YOU SHOULD NOT EDIT THIS CLASS!
    """
    def __init__(self, scene):

        self.scene = scene
        

        # save current working directory
        cwd = os.getcwd()

        # Initialize the library
        if not glfw.init():
            return

        # restore cwd
        os.chdir(cwd)

        # buffer hints
        glfw.window_hint(glfw.DEPTH_BITS, 32)

        # define desired frame rate
        self.frame_rate = 60

        # OS X supports only forward-compatible core profiles from 3.2
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)
        glfw.window_hint(glfw.COCOA_RETINA_FRAMEBUFFER, False)

        # make a window
        self.width, self.height = scene.width, scene.height
        self.window = glfw.create_window(self.width, self.height, scene.scene_title, None, None)
        if not self.window:
            self.impl.shutdown()
            glfw.terminate()
            return

        # Make the window's context current
        glfw.make_context_current(self.window)

        # initializing imgui
        imgui.create_context()
        self.impl = GlfwRenderer(self.window)

        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.onMouseButton)
        glfw.set_key_callback(self.window, self.onKeyboard)
        glfw.set_window_size_callback(self.window, self.onSize)

        # create modernGL context and initialize GL objects in scene
        self.ctx = mgl.create_context()
        self.ctx.enable(flags=mgl.PROGRAM_POINT_SIZE)
        self.scene.init_gl(self.ctx)
        mgl.DEPTH_TEST = True

        # exit flag
        self.exitNow = False


    def onMouseButton(self, win, button, action, mods):
        # Don't react to clicks on UI controllers
        if not imgui.get_io().want_capture_mouse:
            #print("mouse button: ", win, button, action, mods)
            if action == glfw.PRESS:
                x, y = glfw.get_cursor_pos(win)
                p = [int(x), int(y)]
                self.scene.add_point(p)


    def onKeyboard(self, win, key, scancode, action, mods):
        #print("keyboard: ", win, key, scancode, action, mods)

        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            # clear everything
            if key == glfw.KEY_C:
                self.scene.clear()
            if key == glfw.KEY_S:
                self.scene.show_spline = not self.scene.show_spline
            if key == glfw.KEY_K and mods != glfw.MOD_SHIFT:
                if self.scene.order > 1:
                    self.scene.order -= 1
                    print("Changing order down to ", self.scene.order)
                    if len(self.scene.points) >= self.scene.order:
                        self.scene.points_on_bezier_curve = self.scene.bezier_curve_callback(self.scene.order, self.scene.points, self.scene.knotVector_calc(), self.scene.curve_points)
            if mods == glfw.MOD_SHIFT:
                if key == glfw.KEY_K:
                    self.scene.order += 1
                    print("Changing order up to ", self.scene.order)
                    if len(self.scene.points) >= self.scene.order:
                        self.scene.points_on_bezier_curve = self.scene.bezier_curve_callback(self.scene.order, self.scene.points, self.scene.knotVector_calc(), self.scene.curve_points)
            if key == glfw.KEY_M and mods != glfw.MOD_SHIFT:
                if self.scene.curve_points > 1:
                    self.scene.curve_points -= 1
                    print("Changing curve points amount down to ", self.scene.curve_points)
                    if len(self.scene.points) >= self.scene.order:
                        self.scene.points_on_bezier_curve = self.scene.bezier_curve_callback(self.scene.order, self.scene.points, self.scene.knotVector_calc(), self.scene.curve_points)
            if mods == glfw.MOD_SHIFT:
                if key == glfw.KEY_M:
                    self.scene.curve_points += 1
                    print("Changing curve points amount up to ", self.scene.curve_points)
                    if len(self.scene.points) >= self.scene.order:
                        self.scene.points_on_bezier_curve = self.scene.bezier_curve_callback(self.scene.order, self.scene.points, self.scene.knotVector_calc(), self.scene.curve_points)
            



    def onSize(self, win, width, height):
        #print("onsize: ", win, width, height)
        self.width          = width
        self.height         = height
        self.ctx.viewport   = (0, 0, self.width, self.height)
        self.scene.resize(width, height)


    def run(self):
        # initializer timer
        glfw.set_time(0.0)
        t = 0.0
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # update every x seconds
            currT = glfw.get_time()
            if currT - t > 1.0 / self.frame_rate:
                # update time
                t = currT

                # == Frame-wise IMGUI Setup ===
                imgui.new_frame()                   # Start new frame context
                imgui.begin("Controller")     # Start new window context

                # Define UI Elements
                if imgui.button("Clear (C)"):
                    self.scene.clear()

                if imgui.button("Show Spline (S)"):
                    self.scene.show_spline = not self.scene.show_spline

                if imgui.button("order +1 (Shift + K)"):
                    self.scene.order += 1
                    print("Changing order up to ", self.scene.order)
                    if len(self.scene.points) >= self.scene.order:
                        self.scene.points_on_bezier_curve = self.scene.bezier_curve_callback(self.scene.order, self.scene.points, self.scene.knotVector_calc(), self.scene.curve_points)

                if imgui.button("order -1 (K)"):
                    if self.scene.order > 1:
                        self.scene.order -= 1
                        print("Changing order down to ", self.scene.order)
                        if len(self.scene.points) >= self.scene.order:
                            self.scene.points_on_bezier_curve = self.scene.bezier_curve_callback(self.scene.order, self.scene.points, self.scene.knotVector_calc(),self.scene.curve_points)
                if imgui.button("curve points +1 (Shift + M)"):
                    self.scene.curve_points += 1
                    print("Changing curve points amount up to ", self.scene.curve_points)
                    if len(self.scene.points) >= self.scene.order:
                        self.scene.points_on_bezier_curve = self.scene.bezier_curve_callback(self.scene.order, self.scene.points, self.scene.knotVector_calc(), self.scene.curve_points)
                if imgui.button("curve points -1 (M)"):
                    if self.scene.curve_points > 1:
                        self.scene.curve_points -= 1
                        print("Changing curve points amount down to ", self.scene.curve_points)
                        if len(self.scene.points) >= self.scene.order:
                            self.scene.points_on_bezier_curve = self.scene.bezier_curve_callback(self.scene.order, self.scene.points, self.scene.knotVector_calc(), self.scene.curve_points)
            


                imgui.end()                         # End window context
                imgui.render()                      # Run render callback
                imgui.end_frame()                   # End frame context
                self.impl.process_inputs()          # Poll for UI events

                # == Rendering GL ===
                glfw.poll_events()                  # Poll for GLFW events
                self.ctx.clear()                    # clear viewport
                self.scene.render()                 # render scene
                self.impl.render(imgui.get_draw_data()) # render UI
                glfw.swap_buffers(self.window)      # swap front and back buffer


        # end
        self.impl.shutdown()
        glfw.terminate()
