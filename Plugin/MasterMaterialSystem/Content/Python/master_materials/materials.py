from master_materials import (
    assets,
    constants,
    menus
)

from master_materials.unreal_systems import (
    AssetEditorSubsystem,
    EditorAssetSubsystem
)

import unreal


# Utility class to make material parameters more convenient to interact with
class MaterialParamInfo:
    material = None
    data = dict()
    nodes = dict()

    def __init__(self, material):
        self.material = material
        self.is_material_instance = isinstance(material, unreal.MaterialInstance)

        # Find the actual parent material if dealing with a Material Instance
        self.parent_material = self.material
        if self.is_material_instance:
            for x in range(100):
                self.parent_material = self.parent_material.parent
                if isinstance(self.parent_material, unreal.Material):
                    break

        self.populate_data()

    def populate_data(self):
        """Populate the data from the material graph"""
        self.data = dict()

        # Loop through each final output node of the parent material
        for attr_member in dir(unreal.MaterialProperty):
            if attr_member.startswith("MP_"):
                end_node = unreal.MaterialEditingLibrary.get_material_property_input_node(
                    self.parent_material,
                    getattr(unreal.MaterialProperty, attr_member)
                )
                self.walk_node(end_node)

    def walk_node(self, node):
        """Walk up the node connection (end -> start) looking for param info"""
        if not node:
            return

        # Register any parameter nodes that are found
        if isinstance(node, unreal.MaterialExpressionParameter)\
                or isinstance(node, unreal.MaterialExpressionTextureSampleParameter):
            group_name = str(node.get_editor_property("group"))
            property_name = str(node.get_editor_property("parameter_name"))
            self.data.setdefault(group_name, [])
            if property_name not in self.data[group_name]:
                self.data[group_name].append(property_name)
                self.nodes[property_name] = node

        # Walk up the node chain
        for item in unreal.MaterialEditingLibrary.get_inputs_for_material_expression(self.parent_material, node):
            self.walk_node(item)

    def get_node(self, parameter):
        """Get the graph node for the given parameter"""
        node = self.nodes.get(parameter)
        if node:
            return node

        raise ValueError(f"`{parameter}` not found on {self.parent_material.get_path_name()}!")

    def get_parameter_names(self):
        """Get all parameter names on this material"""
        parameter_names = []
        for k, v in self.data.items():
            parameter_names.extend(v)

        return sorted(parameter_names)

    def get_parameter_group(self, parameter):
        """Get a given parameter's group"""
        node = self.get_node(parameter)

        return node.get_editor_property("group")

    def get_parameter_type(self, parameter):
        """Get the data type of the given parameter"""
        node = self.get_node(parameter)

        if isinstance(node, unreal.MaterialExpressionScalarParameter):
            return float
        elif isinstance(node, unreal.MaterialExpressionStaticSwitchParameter):
            return bool
        elif isinstance(node, unreal.MaterialExpressionTextureSampleParameter2D):
            return unreal.Texture
        elif isinstance(node, unreal.MaterialExpressionVectorParameter):
            return unreal.LinearColor

    def get_parameter_value(self, parameter):
        """Get the value of the given parameter"""
        node_type = self.get_parameter_type(parameter)

        if self.is_material_instance:
            if node_type == float:
                return unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(self.material, parameter)
            elif node_type == bool:
                return unreal.MaterialEditingLibrary.get_material_instance_static_switch_parameter_value(self.material, parameter)
            elif node_type == unreal.Texture:
                return unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(self.material, parameter)
            elif node_type == unreal.LinearColor:
                return unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(self.material, parameter)
        else:
            if node_type == float:
                return unreal.MaterialEditingLibrary.get_material_default_scalar_parameter_value(self.parent_material, parameter)
            elif node_type == bool:
                return unreal.MaterialEditingLibrary.get_material_default_static_switch_parameter_value(self.parent_material, parameter)
            elif node_type == unreal.Texture:
                return unreal.MaterialEditingLibrary.get_material_default_texture_parameter_value(self.parent_material, parameter)
            elif node_type == unreal.LinearColor:
                return unreal.MaterialEditingLibrary.get_material_default_vector_parameter_value(self.parent_material, parameter)

    def set_parameter_value(self, parameter, value):
        """Set the value of the given parameter"""

        # convert ints to floats if needed
        if isinstance(value, int):
            value = float(value)

        if not isinstance(value, self.get_parameter_type(parameter)):
            raise ValueError(f"parameter expects a `{self.get_parameter_type(parameter)}` value, received `{type(value)}`")

        if value == self.get_parameter_value(parameter):
            # nothing to do here
            return

        node_type = self.get_parameter_type(parameter)

        # handle Material Instances
        if self.is_material_instance:
            if node_type == float:
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(self.material, parameter, value)
            elif node_type == bool:
                unreal.MaterialEditingLibrary.set_material_instance_static_switch_parameter_value(self.material, parameter, value)
            elif node_type == unreal.Texture:
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(self.material, parameter, value)
            elif node_type == unreal.LinearColor:
                unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(self.material, parameter, value)
            else:
                raise ValueError(f"Unhandled type {node_type} for parameter {parameter} on {self.material}")

            EditorAssetSubsystem.save_loaded_asset(self.material)

        # handle normal materials
        else:
            node = self.get_node(parameter)
            if node_type == unreal.Texture:
                node.set_editor_property("texture", value)
            else:
                node.set_editor_property("default_value", value)
            EditorAssetSubsystem.save_loaded_asset(self.parent_material)

        self.refresh_editor_window()

    def refresh_editor_window(self):
        """Refresh the editor window if the material or its parent is currently open in the Editor"""
        if AssetEditorSubsystem.close_all_editors_for_asset(self.material):
            AssetEditorSubsystem.open_editor_for_assets([self.material])

        if self.is_material_instance:
            unreal.MaterialEditingLibrary.update_material_instance(self.material)
        else:
            unreal.MaterialEditingLibrary.recompile_material(self.parent_material)


def register_master_material(material, display_name=""):
    """
    Register the given material in the Master Material System

    parameters:
        material (unreal.Material): the master material to register
    """
    if not display_name:
        display_name = material.get_name()

    assets.set_metadata(material, constants.META_IS_MASTER_MATERIAL, True)
    assets.set_metadata(material, constants.META_MATERIAL_DISPLAY_NAME, display_name)
    menus.setup_menus()


def unregister_master_material(material):
    """
    Unregister the given material in the Master Material System

    parameters:
        material (unreal.Material): the master material to unregister
    """
    assets.set_metadata(material, constants.META_IS_MASTER_MATERIAL, False)
    menus.setup_menus()
