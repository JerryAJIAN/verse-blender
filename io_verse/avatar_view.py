# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


"""
This file contain methods and classes for visualization of other
users connected to Verse server. It visualize their position and
current view to active 3DView. Other Blender users sharing data at
Verse server can also see, where you are and what you do.
"""


if "bpy" in locals():
    import imp
    imp.reload(vrsent)
else:
    import bpy
    import bgl
    import mathutils
    import math
    import verse as vrs
    from .vrsent import vrsent


def draw_cb(self, context):
    """
    This callback function is called, when view to 3d scene is changed
    """

    # This callback works only for 3D View
    if context.area.type != 'VIEW_3D':
        return
    
    # If avatar view of this client doesn't exist yet, then try to 
    # get it
    if self.avatar_view is None:
        self.avatar_view = AvatarView.my_view()
    
    # Update information about avatar's view, when needed
    self.avatar_view.update(context)


class AvatarView(vrsent.VerseNode):
    """
    Verse node with representation of avatar view to 3D View
    """

    # View of own avatar
    __my_view = None

    # Dictionary of other avatar views of other users
    __other_views = {}


    @classmethod
    def my_view(cls):
        """
        Getter of class memeber __my_view
        """
        return __class__.__my_view


    @classmethod
    def other_views(cls):
        """
        Getter of class memeber __other_views
        """
        return __class__.__other_views


    def __init__(self, session, my_view=False, *args, **kwargs):
        """
        Constructor of AvatarView node
        """

        super(AvatarView, self).__init__(session, *args, **kwargs)

        if my_view == True:

            # Create tag group containing informatin about view
            self.view_tg = vrsent.VerseTagGroup(node=self, \
                custom_type=321)

            # Create tags with data of view to 3D view
            self.location = vrsent.VerseTag(tg=self.view_tg, \
                data_type=vrs.VALUE_TYPE_REAL32, \
                value=(0.0, 0.0, 0.0), \
                custom_type=0)
            self.rotation = vrsent.VerseTag(tg=self.view_tg, \
                data_type=vrs.VALUE_TYPE_REAL32, \
                value=(0.0, 0.0, 0.0, 0.0), \
                custom_type=1)
            self.distance = vrsent.VerseTag(tg=self.view_tg, \
                data_type=vrs.VALUE_TYPE_REAL32, \
                value=(0.0,), \
                custom_type=2)
            self.perspective = vrsent.VerseTag(tg=self.view_tg, \
                data_type=vrs.VALUE_TYPE_STRING8, \
                value=('PERSP',), \
                custom_type=3)
            self.width = vrsent.VerseTag(tg=self.view_tg, \
                data_type=vrs.VALUE_TYPE_UINT16, \
                value=(0,), \
                custom_type=4)
            self.height = vrsent.VerseTag(tg=self.view_tg, \
                data_type=vrs.VALUE_TYPE_UINT16, \
                value=(0,), \
                custom_type=5)
            self.lens = vrsent.VerseTag(tg=self.view_tg, \
                data_type=vrs.VALUE_TYPE_REAL32, \
                value=(0.0,), \
                custom_type=6)
            self.scene_node_id = vrsent.VerseTag(tg=self.view_tg, \
                data_type=vrs.VALUE_TYPE_UINT32, \
                value=(0,), \
                custom_type=7)

            self.cur_screen = None
            self.cur_area = None

            __class__.__my_view = self
        else:
            try:
                __class__.__other_views[kwargs['node_id']] = self
            except KeyError:
                # TODO: this should not happen
                pass
            # TODO: handle this situation better.
            # We know that these tag group and tags will be probably created,
            # but we cannnot creat them ... other client has to do this and
            # server has to send them to this client
            self.view_tg = None
            self.location = None
            self.rotation = None
            self.distance = None
            self.perspective = None
            self.width = None
            self.height = None
            self.lens = None
            self.scene_node_id = None

        self.my_view = my_view
        self.scene_node = None

        try:
            verse_user = session.users[self.user_id]
        except KeyError:
            username = "User"
        else:
            username = verse_user.name
        wm = bpy.context.window_manager
        wm.verse_avatars.add()
        wm.verse_avatars[-1].name = username + '@' # TODO: update, when corespondig tag values are set
        wm.verse_avatars[-1].node_id = self.id
        # TODO: tag View3d to update


    def update(self, context):
        """
        This method tries to update members according context
        """
        
        self.cur_screen = context.screen
        self.cur_area = context.area
        
        # Location of avatar
        if tuple(context.space_data.region_3d.view_location) != self.location.value:
            self.location.value = tuple(context.space_data.region_3d.view_location)
    
        # Rotation around location point
        if tuple(context.space_data.region_3d.view_rotation) != self.rotation.value:
            self.rotation.value = tuple(context.space_data.region_3d.view_rotation)
    
        # Distance from location point
        if context.space_data.region_3d.view_distance != self.distance.value[0]:
            self.distance.value = (context.space_data.region_3d.view_distance,)
        
        # Perspective/Ortho
        if context.space_data.region_3d.view_perspective != self.perspective.value[0]:
            print(context.space_data.region_3d.view_perspective)
            self.persp.value = (context.space_data.region_3d.view_perspective,)
        
        # Lens
        if context.space_data.lens != self.lens.value[0]:
            self.lens.value = (context.space_data.lens,)
                
        # Width
        if context.area.width != self.width.value[0]:
            self.width.value = (context.area.width,)
        
        # Height
        if context.area.height != self.height.value[0]:
            self.height.value = (context.area.height,)    

        # TODO: Update scene
        #if context.scene.verse_scene_node_id != self.scene_node_id[0]:
        #    self.scene_node_id = (context.scene.verse_scene_node_id,)

        
    def draw(self, area, region_data, space):
        """
        Draw avatar view in given context
        """
        
        color = (0.0, 0.0, 1.0, 1.0)
        alpha = 2.0*math.atan((18.0/2.0)/self.lens.value[0])
        dist = 0.5/(math.tan(alpha/2.0))
        height = 1.0
        width = self.width.value[0]/self.height.value[0]
                    
        points = {}
        points['border'] = [None, None, None, None]
        points['center'] = [None]
        
        # Points of face
        if self.active is True:
            points['right_eye'] = [mathutils.Vector((0.25, 0.25, self.distance.value[0] - dist)), \
                mathutils.Vector((0.3, 0.25, self.distance.value[0] - dist)), \
                mathutils.Vector((0.3, 0.0, self.distance.value[0] - dist)), \
                mathutils.Vector((0.25, 0.0, self.distance.value[0] - dist)), \
                mathutils.Vector((0.25, 0.25, self.distance.value[0] - dist))]
            points['left_eye'] = [mathutils.Vector((-0.25, 0.25, self.distance.value[0] - dist)), \
                mathutils.Vector((-0.3, 0.25, self.distance.value[0] - dist)), \
                mathutils.Vector((-0.3, 0.0, self.distance.value[0] - dist)), \
                mathutils.Vector((-0.25, 0.0, self.distance.value[0] - dist)), \
                mathutils.Vector((-0.25, 0.25, self.distance.value[0] - dist))]
        else:
            points['right_eye'] = [mathutils.Vector((0.1569932997226715, 0.1604899913072586, self.distance.value[0] - dist)), \
                mathutils.Vector((0.19806477427482605, 0.14419437944889069, self.distance.value[0] - dist)), \
                mathutils.Vector((0.2499999850988388, 0.13702455163002014, self.distance.value[0] - dist)), \
                mathutils.Vector((0.30193519592285156, 0.1441943645477295, self.distance.value[0] - dist)), \
                mathutils.Vector((0.3430066704750061, 0.1604899764060974, self.distance.value[0] - dist))]
            points['left_eye'] = [mathutils.Vector((-0.1569932997226715, 0.1604899913072586, self.distance.value[0] - dist)), \
                mathutils.Vector((-0.19806477427482605, 0.14419437944889069, self.distance.value[0] - dist)), \
                mathutils.Vector((-0.2499999850988388, 0.13702455163002014, self.distance.value[0] - dist)), \
                mathutils.Vector((-0.30193519592285156, 0.1441943645477295, self.distance.value[0] - dist)), \
                mathutils.Vector((-0.3430066704750061, 0.1604899764060974, self.distance.value[0] - dist))]
        
        points['mouth'] = [mathutils.Vector((-0.40912365913391113, -0.11777058243751526, self.distance.value[0] - dist)), \
            mathutils.Vector((-0.3441678285598755, -0.15873458981513977, self.distance.value[0] - dist)), \
            mathutils.Vector((-0.2563667893409729, -0.1998385488986969, self.distance.value[0] - dist)), \
            mathutils.Vector((-0.18191590905189514, -0.22385218739509583, self.distance.value[0] - dist)), \
            mathutils.Vector((-0.10375960171222687, -0.23957833647727966, self.distance.value[0] - dist)), \
            mathutils.Vector((0.0, -0.2464955747127533, self.distance.value[0] - dist)), \
            mathutils.Vector((0.10375960171222687, -0.23957833647727966, self.distance.value[0] - dist)), \
            mathutils.Vector((0.18191590905189514, -0.22385218739509583, self.distance.value[0] - dist)), \
            mathutils.Vector((0.2563667893409729, -0.1998385488986969, self.distance.value[0] - dist)), \
            mathutils.Vector((0.3441678285598755, -0.15873458981513977, self.distance.value[0] - dist)), \
            mathutils.Vector((0.40912365913391113, -0.11777058243751526, self.distance.value[0] - dist))]            
                
        # Put border points of camera to basic position
        points['border'][0] = mathutils.Vector((-width/2.0, \
            -0.5, \
            self.distance.value[0] - dist,
            1.0))
        points['border'][1] = mathutils.Vector((width/2.0, \
            -0.5, \
            self.distance.value[0] - dist,
            1.0))
        points['border'][2] = mathutils.Vector((width/2.0, \
            0.5, \
            self.distance.value[0] - dist, \
            1.0))
        points['border'][3] = mathutils.Vector((-width/2.0, \
            0.5, \
            self.distance.value[0] - dist, \
            1.0))
        
        # Center of view
        points['center'][0] = mathutils.Vector((0.0, \
            0.0, \
            self.distance.value[0], \
            1.0))        
        
        # Create transformation (rotation) matrix
        rot_matrix = mathutils.Quaternion(self.rotation.value).to_matrix().to_4x4()
        
        # Transform points in all point groups
        for point_group in points.values():
            for index in range(len(point_group)):
                # Rotate points
                point_group[index] = (rot_matrix*point_group[index]).to_3d()
                # Move points
                point_group[index] += mathutils.Vector(self.location.value)
        
        # Get & convert the Perspective Matrix of the current view/region.
        perspMatrix = region_data.perspective_matrix
        tempMat = [perspMatrix[j][i] for i in range(4) for j in range(4)]
        perspBuff = bgl.Buffer(bgl.GL_FLOAT, 16, tempMat)
    
        # Store previous OpenGL settings.
        # Store MatrixMode
        MatrixMode_prev = bgl.Buffer(bgl.GL_INT, [1])
        bgl.glGetIntegerv(bgl.GL_MATRIX_MODE, MatrixMode_prev)
        MatrixMode_prev = MatrixMode_prev[0]
    
        # Store projection matrix
        ProjMatrix_prev = bgl.Buffer(bgl.GL_DOUBLE, [16])
        bgl.glGetFloatv(bgl.GL_PROJECTION_MATRIX, ProjMatrix_prev)
    
        # Store Line width
        lineWidth_prev = bgl.Buffer(bgl.GL_FLOAT, [1])
        bgl.glGetFloatv(bgl.GL_LINE_WIDTH, lineWidth_prev)
        lineWidth_prev = lineWidth_prev[0]
    
        # Store GL_BLEND
        blend_prev = bgl.Buffer(bgl.GL_BYTE, [1])
        bgl.glGetFloatv(bgl.GL_BLEND, blend_prev)
        blend_prev = blend_prev[0]
        
        # Store GL_DEPTH_TEST
        depth_test_prev = bgl.Buffer(bgl.GL_BYTE, [1])
        bgl.glGetFloatv(bgl.GL_DEPTH_TEST, depth_test_prev)
        depth_test_prev = depth_test_prev[0]
            
        # Store GL_LINE_STIPPLE
        line_stipple_prev = bgl.Buffer(bgl.GL_BYTE, [1])
        bgl.glGetFloatv(bgl.GL_LINE_STIPPLE, line_stipple_prev)
        line_stipple_prev = line_stipple_prev[0]
    
        # Store glColor4f
        col_prev = bgl.Buffer(bgl.GL_FLOAT, [4])
        bgl.glGetFloatv(bgl.GL_COLOR, col_prev)
        
        # Prepare for 3D drawing
        bgl.glLoadIdentity()
        bgl.glMatrixMode(bgl.GL_PROJECTION)
        bgl.glLoadMatrixf(perspBuff)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
                
        # Draw "Look At" point
        bgl.glLineWidth(1)
        bgl.glBegin(bgl.GL_LINES)
        bgl.glColor4f(color[0], color[1], color[2], color[3])
        
        bgl.glVertex3f(self.location.value[0]+0.1, \
            self.location.value[1], \
            self.location.value[2])
        bgl.glVertex3f(self.location.value[0]-0.1, \
            self.location.value[1], \
            self.location.value[2])
        
        bgl.glVertex3f(self.location.value[0], \
            self.location.value[1]+0.1, \
            self.location.value[2])
        bgl.glVertex3f(self.location.value[0], \
            self.location.value[1]-0.1, \
            self.location.value[2])
        
        bgl.glVertex3f(self.location.value[0], \
            self.location.value[1], \
            self.location.value[2]+0.1)
        bgl.glVertex3f(self.location.value[0], \
            self.location.value[1], \
            self.location.value[2]-0.1)
        
        bgl.glEnd()
        
        border = points['border']
        center = points['center']
        
        # Draw border of camera
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex3f(border[0][0], border[0][1], border[0][2])
        bgl.glVertex3f(border[1][0], border[1][1], border[1][2])
        bgl.glVertex3f(border[2][0], border[2][1], border[2][2])
        bgl.glVertex3f(border[3][0], border[3][1], border[3][2])
        bgl.glVertex3f(border[0][0], border[0][1], border[0][2])
        bgl.glEnd()
        
        # Draw left eye
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for point in points['left_eye']:
            bgl.glVertex3f(point[0], point[1], point[2])
        bgl.glEnd()

        # Draw right eye
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for point in points['right_eye']:
            bgl.glVertex3f(point[0], point[1], point[2])
        bgl.glEnd()
        
        # Draw mouth
        bgl.glBegin(bgl.GL_LINE_STRIP)
        for point in points['mouth']:
            bgl.glVertex3f(point[0], point[1], point[2])
        bgl.glEnd()
        
        # Draw dashed lines from center of "camera" to border of camera        
        bgl.glEnable(bgl.GL_LINE_STIPPLE)
        bgl.glBegin(bgl.GL_LINES)
        bgl.glVertex3f(border[0][0], border[0][1], border[0][2])
        bgl.glVertex3f(center[0][0], center[0][1], center[0][2])
        bgl.glVertex3f(border[1][0], border[1][1], border[1][2])
        bgl.glVertex3f(center[0][0], center[0][1], center[0][2])
        bgl.glVertex3f(border[2][0], border[2][1], border[2][2])
        bgl.glVertex3f(center[0][0], center[0][1], center[0][2])
        bgl.glVertex3f(border[3][0], border[3][1], border[3][2])
        bgl.glVertex3f(center[0][0], center[0][1], center[0][2])
        bgl.glEnd()
        
        # Draw dashed line from Look At point and center of camera
        bgl.glBegin(bgl.GL_LINES)
        bgl.glVertex3f(self.location[0], \
            self.location[1], \
            self.location[2])
        bgl.glVertex3f(center[0][0], center[0][1], center[0][2])
        bgl.glEnd()
        bgl.glDisable(bgl.GL_LINE_STIPPLE)
    
        # Restore previous OpenGL settings
        bgl.glLoadIdentity()
        bgl.glMatrixMode(MatrixMode_prev)
        bgl.glLoadMatrixf(ProjMatrix_prev)
        bgl.glLineWidth(lineWidth_prev)
        if not blend_prev:
            bgl.glDisable(bgl.GL_BLEND)
        if not line_stipple_prev:
            bgl.glDisable(bgl.GL_LINE_STIPPLE)
        if not depth_test_prev:
            bgl.glDisable(bgl.GL_DEPTH_TEST)
        bgl.glColor4f(col_prev[0], col_prev[1], col_prev[2], col_prev[3])


class VerseAvatarStatus(bpy.types.Operator):
    """
    Status operator of Verse avatar
    """
    bl_idname = "view3d.verse_avatar"
    bl_label = "Capture"
    bl_description = "Capture camera position"
    last_activity = 'NONE'
    
    _handle = None
    
    def __init__(self):
        """
        Constructor of this operator
        """
        self.avatar_view = None
    
    def modal(self, context, event):
        """
        This method is executed on events
        """
        return {'PASS_THROUGH'}
    
    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True and AvatarView.my_view() is not None:
            return True
        else:
            return False

    def invoke(self, context, event):
        """
        This method is used, when this operator is executed
        """
        if context.area.type == 'VIEW_3D':
            if context.window_manager.verse_avatar_capture is False:
                context.window_manager.verse_avatar_capture = True
                # Register callback function
                VerseAvatarStatus._handle = bpy.types.SpaceView3D.draw_handler_add(draw_cb, (self, context), 'WINDOW', 'POST_PIXEL')
                print('add handle ...', VerseAvatarStatus._handle)
                # Force redraw (display bgl stuff)
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                return {'RUNNING_MODAL'}
            else:
                context.window_manager.verse_avatar_capture = False
                # Unregister callback function
                print('remove handle ...', VerseAvatarStatus._handle)
                bpy.types.SpaceView3D.draw_handler_remove(VerseAvatarStatus._handle, 'WINDOW')
                self._handle = None
                # Force redraw (not display bgl stuff)
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.tag_redraw()
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "3D View not found, can't run Camera Capture")
            return {'CANCELLED'}
     
    def cancel(self, context):
        """
        This method is called, when operator is canceled.
        """
        print('cancel()')
        if context.window_manager.verse_avatar_capture is True:
            context.window_manager.verse_avatar_capture = False
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}


class VERSE_AVATAR_OT_show(bpy.types.Operator):
    """
    This operator show selected avatar
    """
    bl_idname = 'view3d.verse_avatar_show'
    bl_label = 'Show Avatar'

    def invoke(self, context, event):
        """
        Show avatar selected in list of avatars
        """
        wm = context.window_manager
        avatar = wm.verse_avatars[wm.cur_verse_avatar_index]
        avatar.visualized = True
        # TODO: subscribe to tag group
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True and wm.cur_verse_avatar_index != -1:
            if wm.verse_avatars[wm.cur_verse_avatar_index].visualized == False:
                return True
            else:
                return False
        else:
            return False


class VERSE_AVATAR_OT_show_all(bpy.types.Operator):
    """
    This operator show all avatars
    """
    bl_idname = 'view3d.verse_avatar_show_all'
    bl_label = 'Show All Avatars'

    def invoke(self, context, event):
        """
        Show all avatars in list of avatars
        """
        wm = context.window_manager
        for avatar in wm.verse_avatars:
            avatar.visualized = True
        # TODO: subscribe to unsubscribed tag groups
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True:
            return True
        else:
            return False


class VERSE_AVATAR_OT_hide(bpy.types.Operator):
    """
    This operator hide selected avatar
    """
    bl_idname = 'view3d.verse_avatar_hide'
    bl_label = 'Hide Avatar'

    def invoke(self, context, event):
        """
        Hide avatar selected in list of avatars
        """
        wm = context.window_manager
        avatar = wm.verse_avatars[wm.cur_verse_avatar_index]
        avatar.visualized = False
        # TODO: unsubscribe from tag group
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True and wm.cur_verse_avatar_index != -1:
            if wm.verse_avatars[wm.cur_verse_avatar_index].visualized == True:
                return True
            else:
                return False
        else:
            return False


class VERSE_AVATAR_OT_hide_all(bpy.types.Operator):
    """
    This operator hide all avatars
    """
    bl_idname = 'view3d.verse_avatar_hide_all'
    bl_label = 'Hide All Avatars'

    def invoke(self, context, event):
        """
        Hide all avatars in list of avatars
        """
        wm = context.window_manager
        for avatar in wm.verse_avatars:
            avatar.visualized = False
        # TODO: unsubscribe from all tag groups
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        wm = context.window_manager
        if wm.verse_connected == True:
            return True
        else:
            return False


class VERSE_AVATAR_MT_menu(bpy.types.Menu):
    """
    Menu for verse avatar list
    """
    bl_idname = 'view3d.verse_avatar_menu'
    bl_label = "Shape Key Specials"

    def draw(self, context):
        """
        Draw menu
        """
        layout = self.layout
        layout.operator('view3d.verse_avatar_hide')
        layout.operator('view3d.verse_avatar_hide_all')
        layout.operator('view3d.verse_avatar_show')
        layout.operator('view3d.verse_avatar_show_all')

    @classmethod
    def poll(cls, context):
        """
        This class method is used, when Blender check, if this operator can be
        executed
        """
        # Return true only in situation, when client is connected to Verse server
        if AvatarView.my_view() is not None:
            return True
        else:
            return False


class VERSE_AVATAR_NODES_list_item(bpy.types.PropertyGroup):
    """
    Group of properties with representation of Verse avatar node
    """
    name = bpy.props.StringProperty( \
        name = "Username", \
        description = "Username of connected avatar", \
        default = "User Name")
    visualized = bpy.props.BoolProperty( \
        name = "Visualized", \
        description = "Is avatar visualized in 3D view", \
        default = True)
    node_id = bpy.props.IntProperty( \
        name = "Node ID", \
        description = "Node ID of avatar node", \
        default = -1)


class VERSE_AVATAR_UL_slot(bpy.types.UIList):
    """
    A custom slot with information about Verse avatar node
    """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        verse_avatar = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(verse_avatar.name, icon='ARMATURE_DATA')
            if verse_avatar.visualized == True:
                layout.operator('view3d.verse_avatar_hide', text='', icon='RESTRICT_VIEW_OFF')
            else:
                layout.operator('view3d.verse_avatar_show', text='', icon='RESTRICT_VIEW_ON')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(verse_avatar.name)


class VerseAvatarPanel(bpy.types.Panel):
    """
    Panel with widgets
    """
    bl_idname = "view3d.verse_avatar_panel"
    bl_label = "Verse Avatar"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    def draw(self, context):
        """
        Define drawing of widgets
        """
        wm = context.window_manager
        layout = self.layout

        # TODO: Remove following button. It should be sent automaticaly
        if not wm.verse_avatar_capture:
            layout.operator("view3d.verse_avatar", text="Start Capture",
                icon = "PLAY")
        else:
            layout.operator("view3d.verse_avatar", text="Pause Capture",
                icon = "PAUSE")

        # Display connected avatars in current scene and
        # display menu to hide/display them in 3d
        row = layout.row()
        row.template_list('VERSE_AVATAR_UL_slot', \
            'verse_avatars_widget_id', \
            wm, \
            'verse_avatars', \
            wm, \
            'cur_verse_avatar_index', \
            rows = 3)

        col = row.column(align=True)
        col.menu('view3d.verse_avatar_menu', icon='DOWNARROW_HLT', text="")


def init_properties():
    """
    Initialize properties used by this module
    """
    wm = bpy.types.WindowManager
    wm.verse_avatar_capture = bpy.props.BoolProperty( \
        name = "Avatar Capture", \
        default = False, \
        description = "Is information about my view to 3D scene shared at Verse server"
    )
    wm.verse_avatars = bpy.props.CollectionProperty( \
        type =  VERSE_AVATAR_NODES_list_item, \
        name = "Verse Avatars", \
        description = "The list of verse avatar nodes representing Blender at Verse server" \
    )
    wm.cur_verse_avatar_index = bpy.props.IntProperty( \
        name = "Index of current Verse avatar", \
        default = -1, \
        min = -1, \
        max = 1000, \
        description = "The index of curently selected Verse avatar node"
    )


def reset_properties():
    """
    Reset properties used by this module
    """
    wm = bpy.types.WindowManager
    wm.verse_avatar_capture = False
    wm.cur_verse_avatar_index = -1


classes = (VERSE_AVATAR_NODES_list_item, \
    VERSE_AVATAR_UL_slot, \
    VerseAvatarPanel, \
    VerseAvatarStatus, \
    VERSE_AVATAR_OT_hide, \
    VERSE_AVATAR_OT_hide_all, \
    VERSE_AVATAR_OT_show, \
    VERSE_AVATAR_OT_show_all, \
    VERSE_AVATAR_MT_menu)


def register():
    """
    Register classes with panel and init properties
    """
    for c in classes:
        bpy.utils.register_class(c)
    init_properties()


def unregister():
    """
    Unregister classes with panel and reset properties
    """
    for c in classes:
        bpy.utils.unregister_class(c)
    reset_properties()


if __name__ == '__main__':
    register()
