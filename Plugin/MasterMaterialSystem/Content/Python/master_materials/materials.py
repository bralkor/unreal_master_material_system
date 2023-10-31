from master_materials import (
    assets,
    constants,
    menus
)

from master_materials.unreal_systems import (
    AssetTools,
    AssetEditorSubsystem,
    EditorAssetSubsystem
)

import unreal


# Utility class to make material parameters more convenient to interact with
class MaterialParamInfo:
    material = None
    parameters = dict()
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
        self.parameters = dict()
        self.nodes = dict()

        # collect parameters as {param_name: data_type}
        self.parameters = {
            str(item): float
            for item in
            unreal.MaterialEditingLibrary.get_scalar_parameter_names(self.material)
        } | {
            str(item): bool
            for item in
            unreal.MaterialEditingLibrary.get_static_switch_parameter_names(self.material)
        } | {
            str(item): unreal.Texture
            for item in
            unreal.MaterialEditingLibrary.get_texture_parameter_names(self.material)
        } | {
            str(item): unreal.LinearColor
            for item in
            unreal.MaterialEditingLibrary.get_vector_parameter_names(self.material)
        }

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
        if isinstance(node, unreal.MaterialExpressionParameter) or isinstance(node, unreal.MaterialExpressionTextureSampleParameter):
            property_name = str(node.get_editor_property("parameter_name"))
            if property_name not in self.nodes:
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
        return sorted([k for k in self.parameters.keys()])

    def get_parameter_type(self, parameter):
        """Get the data type of the given parameter"""
        return self.parameters.get(parameter)

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
            node = self.nodes.get(parameter)
            if self.get_parameter_type(parameter) == unreal.Texture:
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


def create_new_material_instance(destination_folder, master_material, asset_name=None, target_material=None, should_save=True, should_open=True):
    """
    Create a new material instance based on a master material

    parameters:
        destination_folder (str): the folder path of the new asset
        master_material (unreal.Material): the master material to create an instance of
        asset_name (str): If provided, use this name instead of generating one dynamically
        target_material (unreal.MaterialInterface): If provided, a target material to incorporate in the name
        should_save (bool): whether to immediately save the asset after creation
        should_open (bool): whether to open the asset editor

    return:
        unreal.MaterialInstanceConstant: the new material instance asset
    """
    asset_name = asset_name or generate_new_master_material_instance_name(destination_folder, master_material, target_material)

    new_material_instance = AssetTools.create_asset(
        asset_name=asset_name,
        package_path=destination_folder,
        asset_class=unreal.MaterialInstanceConstant,
        factory=unreal.MaterialInstanceConstantFactoryNew()
    )
    if not new_material_instance:
        raise RuntimeError(f"Something went wrong here.... sigh.")
    unreal.MaterialEditingLibrary.set_material_instance_parent(new_material_instance, master_material)

    if should_save:
        assets.save_asset(new_material_instance)

    if should_open:
        AssetEditorSubsystem.open_editor_for_assets([new_material_instance])

    return new_material_instance


def generate_new_master_material_instance_name(destination_folder, master_material, target_material=None):
    """
    Generate a unique name based on the provided Master Material. If a target material is provided it
    will be incorporated in the new name

    parameters:
        destination_folder (str): the Content Browser folder to place the new material
        master_material (unreal.Material): the master material to create a MI name based on
        target_material (unreal.MaterialInterface): If provided, a target material to incorporate in the name

    return:
        str: a unique name to use for the new MI
    """
    # Get the master material name (or reuse
    master_material_name = assets.get_metadata(master_material, constants.META_MATERIAL_DISPLAY_NAME)
    if not master_material_name:
        master_material_name = master_material_name.get_name().split("M_", 1)[-1].split("MI_", 1)[-1]

    new_name = None
    if target_material:
        old_name = target_material.get_name().split("M_", 1)[-1].split("MI_", 1)[-1]
        new_name = f"MI_{master_material_name}_{old_name}".replace(" ", "_")
    else:
        new_name = f"MI_{master_material_name}".replace(" ", "_")

    new_asset_path = f"{destination_folder}/{new_name}"
    return AssetTools.create_unique_asset_name(new_asset_path, "")[1]

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
