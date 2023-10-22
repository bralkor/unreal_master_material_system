import json
from pathlib import Path

from master_materials import (
    constants,
    materials,
    assets
)

from master_materials.unreal_systems import (
    AssetEditorSubsystem,
    EditorUtilitySubsystem
)

import unreal


@unreal.uclass()
class PyMasterMaterialLibrary(unreal.BlueprintFunctionLibrary):
    """
    Container for material related Blueprint Nodes
    """

    @unreal.ufunction(
        ret=unreal.Map(str, unreal.Texture2D),
        params=[unreal.MaterialInterface],
        static=True, meta=dict(Category="Master Materials"), pure=True
    )
    def get_material_texture_map(material) -> dict:
        """Get the texture data for the given material

        parameters:
            material (unreal.Material): the material to query for its texture data
        """
        # For materials get the texture names
        if isinstance(material, unreal.Material):
            return {
                texture.get_name(): texture
                for texture in unreal.MaterialEditingLibrary.get_used_textures(material)
            }

        # For material instances get the parameter names
        if isinstance(material, unreal.MaterialInstanceConstant):
            return {
                param: unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(material, param)
                for param in unreal.MaterialEditingLibrary.get_texture_parameter_names(material)
            }

        return dict()

    @unreal.ufunction(
        ret=unreal.Map(str, unreal.Material),
        static=True, meta=dict(Category="Master Materials")
    )
    def get_all_master_materials() -> dict:
        """Get all master materials as {name: material}"""
        return {
            assets.get_metadata(asset, constants.META_MATERIAL_DISPLAY_NAME): asset.get_asset()
            for asset in assets.find_assets(metadata={constants.META_IS_MASTER_MATERIAL: True}, class_types=["Material"])
        }

    @unreal.ufunction(
        params=[unreal.Material, unreal.MaterialInterface, unreal.Map(str, unreal.Texture), bool],
        static=True, meta=dict(Category="Master Materials")
    )
    def create_material_instance_with_texture_data(master_material, old_material, material_data, replace_references):
        """Create a new instance of the given master material and apply the given texture data to it

        parameters:
            master_material (unreal.Material): the master material to create an instance of
            old_material (unreal.MaterialInterface): the material we want to replace, the new material will be located next to it
            material_data (unreal.Map(str, unreal.Texture)): the {parameter:texture} data to populate the instance with
            replace_references (bool): if True, replace references from the old_material to the newly created instance material
        """

        master_material_name = assets.get_metadata(master_material, constants.META_MATERIAL_DISPLAY_NAME)
        old_name = old_material.get_name().split("M_", 1)[-1].split("MI_", 1)[-1]
        new_name = f"MI_{master_material_name}_{old_name}".replace(" ", "_")

        # create the new material instance
        asset_folder = str(Path(old_material.get_path_name()).parent)
        new_material_instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            asset_name=new_name,
            package_path=asset_folder,
            asset_class=unreal.MaterialInstanceConstant,
            factory=unreal.MaterialInstanceConstantFactoryNew()
        )
        unreal.MaterialEditingLibrary.set_material_instance_parent(new_material_instance, master_material)
        material_info = materials.MaterialParamInfo(new_material_instance)

        # transfer the texture selections from the UI
        for parameter, value in material_data.items():
            if value != unreal.MaterialEditingLibrary.get_material_default_texture_parameter_value(master_material, parameter):
                material_info.set_parameter_value(parameter, value)

        AssetEditorSubsystem.open_editor_for_assets([new_material_instance])
        assets.save_asset(new_material_instance)

        # replace references if checked
        if replace_references:
            updated_assets = []
            asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

            for referencer in asset_registry.get_referencers(
                old_material.get_package().get_path_name(),
                unreal.AssetRegistryDependencyOptions()
            ) or []:
                asset = unreal.load_asset(referencer)

                # Update Static Meshes:
                if isinstance(asset, unreal.StaticMesh):
                    material_slot_name = ""
                    for material in asset.static_materials:
                        if material.material_interface == old_material:
                            material_slot_name = material.material_slot_name
                    material_index = asset.get_material_index(material_slot_name)
                    asset.set_material(material_index, new_material_instance)

                # Update Skeletal Meshes:
                elif isinstance(asset, unreal.SkeletalMesh):
                    new_material_data = []
                    for skeletal_mesh_mat_data in asset.materials:
                        if skeletal_mesh_mat_data.material_interface == old_material:
                            new_material_data.append(
                                unreal.SkeletalMaterial(
                                    new_material_instance,
                                    skeletal_mesh_mat_data.material_slot_name,
                                    skeletal_mesh_mat_data.uv_channel_data
                                )
                            )
                        else:
                            new_material_data.append(skeletal_mesh_mat_data)

                    asset.materials = new_material_data

                    # My incredible hack to force dirty skeletal meshes....
                    tmp = asset.get_editor_property("support_ray_tracing")
                    asset.set_editor_property("support_ray_tracing", not tmp)
                    asset.set_editor_property("support_ray_tracing", not tmp)

                # save the asset
                assets.save_asset(asset)
                updated_assets.append(asset.get_outer().get_name())

            print(f"Updated material assignments on the following assets:")
            for entry in updated_assets:
                print(f"\t{entry}")

        # close tool UI (no longer needed)
        EUW_results = assets.find_assets(
            name="CreateFromMasterMaterial",
            exact_match=True,
            class_types=["EditorUtilityWidgetBlueprint"],
            str_in_path="/MasterMaterialSystem/"
        )
        if EUW_results:
            widget_id = EditorUtilitySubsystem.register_tab_and_get_id(
                unreal.EditorAssetLibrary.load_asset(
                    EUW_results[0].package_name
                )
            )
            EditorUtilitySubsystem.unregister_tab_by_id(widget_id)

        # focus content browser on new material instance
        package_path = new_material_instance.get_package().get_path_name()
        print(f"Created {package_path} from {master_material_name}")
        unreal.EditorAssetLibrary().sync_browser_to_objects([package_path])


    @unreal.ufunction(
        static=True, params=[str, unreal.Map(str, str)],
        meta=dict(Category="Master Materials")
    )
    def save_user_prefs(prefs_name, prefs_data):
        """Python Blueprint Node -- save some basic prefs data"""
        prefs = {
            str(key): str(value)
            for key, value in prefs_data.items()
        }

        # save to the project's Saved dir under pytemp
        prefs_file = Path(
            unreal.Paths.project_saved_dir(),
            "pytemp",
            f"unreal_prefs_{prefs_name}.json"
        )

        if not prefs_file.exists():
            prefs_file.parent.mkdir(parents=True, exist_ok=True)

        with prefs_file.open("w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)


    @unreal.ufunction(
        static=True, ret=unreal.Map(str, str), params=[str],
        pure=True, meta=dict(Category="Master Materials")
    )
    def load_user_prefs(prefs_name) :
        """Python Blueprint Node -- load some basic prefs data"""

        # use the same path structure as the save and make sure it exists
        prefs_file = Path(
            unreal.Paths.project_saved_dir(),
            "pytemp",
            f"unreal_prefs_{prefs_name}.json"
        )
        if not prefs_file.exists():
            return {}

        # we can return the dict as-is, Unreal will convert it to a Map(str,str) for us
        return json.loads(prefs_file.read_text())


    @unreal.ufunction(
        static=True, params=[unreal.EditorUtilityWidget],
        meta=dict(Category="Master Materials", DeterminesOutputType="editor_tool", DefaultToSelf="editor_tool")
    )
    def remove_tool_from_unreal_prefs(editor_tool):
        """Python Blueprint Node -- pass a widget's `self` reference to remove it from the Unreal User Prefs INI"""

        # Get the asset path and pass it to the editor_tools module
        editor_tool_path = str(editor_tool.get_class().get_outer().get_path_name())
        tool = unreal.find_asset(editor_tool_path)
        unreal.MasterMaterialSystemBPLibrary.remove_euw_from_user_prefs(tool)
